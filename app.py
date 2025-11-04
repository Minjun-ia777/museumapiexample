import streamlit as st
import requests
import random # Import the random library

# --- Page Configuration ---
# Set the page to wide layout for more space
st.set_page_config(layout="wide", page_title="MET Artwork Explorer")

# --- Constants ---
# Number of items to display per page
ITEMS_PER_PAGE = 10

# --- API Functions (with Caching) ---
# @st.cache_data is CRUCIAL. It prevents the app from re-fetching data
# from the API every time the user interacts with a widget.

@st.cache_data
def get_departments():
    """Fetches the list of departments from the MET API."""
    try:
        response = requests.get("https://collectionapi.metmuseum.org/public/collection/v1/departments")
        response.raise_for_status()  # Raise an error for bad responses
        return response.json().get("departments", [])
    except requests.RequestException as e:
        st.error(f"Error fetching departments: {e}")
        return []

# --- NEW: Function to get all highlights for the "Surprise Me" feature ---
@st.cache_data
def get_all_highlights():
    """Fetches all object IDs that are marked as highlights."""
    try:
        response = requests.get("https://collectionapi.metmuseum.org/public/collection/v1/search?isHighlight=true&q=")
        response.raise_for_status()
        data = response.json()
        return data.get("objectIDs", [])
    except requests.RequestException as e:
        st.error(f"Error fetching highlights: {e}")
        return []

@st.cache_data
def search_artworks(query, department_id, is_highlight, date_begin=None, date_end=None): # Add date params
    """
    Searches the MET API based on query, department, and highlight status.
    Returns a list of object IDs.
    """
    search_url = "https.collectionapi.metmuseum.org/public/collection/v1/search"
    params = {
        'q': query,
        'isHighlight': is_highlight,
        'departmentId': department_id if department_id != "all" else None,
        'dateBegin': date_begin, # Add dateBegin to params
        'dateEnd': date_end     # Add dateEnd to params
    }
    
    # Clean params (API doesn't like None or empty values)
    params = {k: v for k, v in params.items() if v is not None and v != ""}
    if 'departmentId' in params and params['departmentId'] == 'all':
        del params['departmentId']
        
    try:
        response = requests.get(search_url, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("objectIDs", [])
    except requests.RequestException as e:
        st.error(f"Error during search: {e}")
        return []

@st.cache_data
def get_object_details(object_id):
    """Fetches detailed information for a single object ID."""
    object_url = f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{object_id}"
    try:
        response = requests.get(object_url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        # It's common for some objects to fail, so we'll just skip them
        return None

# --- Session State Initialization ---
# This is used to remember the current page number and search results
# even when the app re-runs.

if 'page' not in st.session_state:
    st.session_state.page = 0
if 'search_results' not in st.session_state:
    st.session_state.search_results = []
# Add a new state to track if we're showing fallback results
if 'show_fallback' not in st.session_state:
    st.session_state.show_fallback = False

# --- UI Layout: Sidebar (Filters) ---
st.sidebar.title("🖼️ MET Artwork Explorer")
st.sidebar.header("Search Filters")

# 1. Load departments for the dropdown
departments = get_departments()
dept_map = {dept['displayName']: 
dept['departmentId'] for dept in departments}

# 2. Add "All" option for departments
dept_names.insert(0, "All Departments")
dept_map["All Departments"] = None

# 3. Sidebar widgets
selected_dept_name = st.sidebar.selectbox("Filter by Department:", dept_names)
search_query = st.sidebar.text_input("Search by Keyword:", placeholder="e.g., Van Gogh, armor, cat")

# --- NEW: Date Range Inputs ---
st.sidebar.write("Filter by Year:")
col1, col2 = st.sidebar.columns(2)
with col1:
    date_begin = st.number_input("Start Year", value=None, placeholder="e.g., 1880", step=1)
with col2:
    date_end = st.number_input("End Year", value=None, placeholder="e.g., 1890", step=1)
# --- END NEW: Date Range ---

is_highlight = st.sidebar.checkbox("Show only MET Highlights")

# Get the department ID from the selected name
selected_dept_id = dept_map.get(selected_dept_name)

# 4. Search button
if st.sidebar.button("Search", type="primary"):
    # When search is clicked, reset page to 0 and perform the search
    st.session_state.page = 0
    with st.spinner("Searching for artworks..."):
        # Pass date params to the search function
        object_ids = search_artworks(search_query, selected_dept_id, is_highlight, date_begin, date_end)
        
        # --- NEW FALLBACK LOGIC ---
        # If the user searched for *something* but got no results...
        # Updated condition to include new date filters
        if not object_ids and (search_query or selected_dept_name != "All Departments" or is_highlight or date_begin or date_end):
            # ...set a flag to show a message...
            st.session_state.show_fallback = True
            # ...and instead search for general highlights.
            object_ids = search_artworks(query="", department_id=None, is_highlight=True)
        else:
            # Otherwise, it's a normal search, so no fallback message.
            st.session_state.show_fallback = False
        # --- END NEW LOGIC ---

        st.session_state.search_results = object_ids
        # Clear the cache for object details if a new search is made
        get_object_details.clear()

# --- NEW: "Surprise Me!" Button ---
st.sidebar.divider()
if st.sidebar.button("Surprise Me! 🎲"):
    with st.spinner("Finding a masterpiece..."):
        st.session_state.page = 0
        highlights = get_all_highlights()
        if highlights:
            # Pick one random ID from the highlights
            random_id = random.choice(highlights)
            st.session_state.search_results = [random_id] # Show only the one random artwork
        else:
            st.session_state.search_results = []
        
        st.session_state.show_fallback = False
        get_object_details.clear()
        st.rerun() # Rerun to reflect the new state immediately
# --- END NEW ---


# --- UI Layout: Main Content (Results) ---
st.title("Artwork Results")

# --- NEW: Display Fallback Message ---
if st.session_state.show_fallback:
    st.warning("No direct matches found for your query. Showing popular highlights instead.")
    st.session_state.show_fallback = False # Reset the flag so it only shows once

# Display a message if no search has been run
if not st.session_state.search_results:
    st.info("Use the sidebar to search for artworks in the MET collection.")
else:
    # Get the list of IDs from session state
    object_ids = st.session_state.search_results
    total_results = len(object_ids)
    
    if total_results == 0:
        st.warning("No results found for your query. Please try different filters.")
    else:
        st.success(f"Found {total_results} matching artworks.")

        # --- Pagination Logic ---
        start_index = st.session_state.page * ITEMS_PER_PAGE
        end_index = min(start_index + ITEMS_PER_PAGE, total_results)
        
        # Get the IDs for the current page
        ids_to_show = object_ids[start_index:end_index]
        
        # Pagination buttons in columns
        col1, col2, col3 = st.columns([1, 2, 1])

        with col1:
            if st.session_state.page > 0:
                if st.button("⬅️ Previous Page"):
                    st.session_state.page -= 1
                    st.rerun() # Re-run the app to show the new page

        with col3:
            if end_index < total_results:
                if st.button("Next Page ➡️"):
                    st.session_state.page += 1
                    st.rerun() # Re-run the app
        
        with col2:
            st.write(f"Showing results {start_index + 1} - {end_index} of {total_results}")

        st.divider()

        # --- Display Results ---
        # Fetch details and display them
        for object_id in ids_to_show:
            details = get_object_details(object_id)
            
            # Check if details were fetched successfully and it has an image
            if details and details.get("primaryImageSmall"):
                
                # Use columns for a clean layout: Image on left, text on right
                img_col, text_col = st.columns([1, 3])
                
                with img_col:
                    st.image(
                        details["primaryImageSmall"],
                        caption=details.get("title", "Untitled")
                    )
                
                with text_col:
                    st.subheader(details.get("title", "Untitled"))
                    
                    # --- NEW: More Details ---
                    st.write(f"**Artist:** {details.get('artistDisplayName', 'Unknown')}")
                    
                    # --- NEW: "More from this Artist" Button ---
                    artist_name = details.get('artistDisplayName')
                    if artist_name and artist_name != "Unknown":
                        if st.button(f"More from {artist_name}", key=f"artist_{object_id}"):
                            st.session_state.page = 0
                            # Search for this artist, clearing other filters
                            with st.spinner(f"Finding more from {artist_name}..."):
                                st.session_state.search_results = search_artworks(
                                    query=artist_name, 
                                    department_id=None, 
                                    is_highlight=False
                                )
                            get_object_details.clear()
                            st.rerun()
                    # --- END NEW ---

                    artist_bio = details.get('artistDisplayBio')
                    if artist_bio:
                        st.write(f"**Artist Bio:** {artist_bio}")
                        
                    st.write(f"**Date:** {details.get('objectDate', 'Unknown')}")
                    st.write(f"**Medium:** {details.get('medium', 'Unknown')}")
                    
                    obj_name = details.get('objectName')
                    if obj_name:
                        st.write(f"**Object Type:** {obj_name}")

                    culture = details.get('culture')
                    if culture:
                        st.write(f"**Culture:** {culture}")

                    period = details.get('period')
                    if period:
                        st.write(f"**Period:** {period}")
                        
                    dims = details.get('dimensions')
                    if dims:
                        st.write(f"**Dimensions:** {dims}")
                    
                    st.write(f"**Department:** {details.get('department', 'Unknown')}")

                    credit = details.get('creditLine')
                    if credit:
                        st.write(f"**Credit Line:** {credit}")
                    # --- END More Details ---
                    
                    # Add a link to the official MET page
                    if details.get("objectURL"):
                        st.link_button("View on MET Website", details["objectURL"])
                
                # --- NEW: Additional Images Gallery ---
                additional_images = details.get("additionalImages")
                if additional_images:
                    st.write("**Additional Images:**")
                    # Create a gallery with up to 4 columns
                    num_images = len(additional_images)
                    cols = st.columns(min(num_images, 4))
                    for i, img_url in enumerate(additional_images[:4]):
                        with cols[i]:
                            st.image(img_url, width=150)
                # --- END Additional Images ---

                # --- NEW: Interactive Tags ---
                tags = details.get("tags")
                if tags and isinstance(tags, list):
                    tag_terms = [tag.get("term") for tag in tags if tag.get("term")]
                    if tag_terms:
                        st.write("**Explore Tags:**")
                        # Use columns to lay out tags, max 5 per row for tidiness
                        num_cols = min(len(tag_terms), 5)
                        tag_cols = st.columns(num_cols)
                        for i, term in enumerate(tag_terms):
                            with tag_cols[i % num_cols]:
                                if st.button(term, key=f"tag_{object_id}_{term}"):
                                    st.session_state.page = 0
                                    with st.spinner(f"Searching for '{term}'..."):
                                        st.session_state.search_results = search_artworks(
                                            query=term,
                                            department_id=None,
                                            is_highlight=False
                                        )
                                    get_object_details.clear()
                                    st.rerun()
                # --- END NEW ---

                st.divider() # Add a line between results

