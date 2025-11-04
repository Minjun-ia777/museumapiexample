import streamlit as st
import requests
import random # Import the random library

# --- Page Configuration ---
# Set the page to wide layout for more space
st.set_page_config(layout="wide", page_title="MET Artwork Explorer")
ITEMS_PER_PAGE = 10

# --- API Functions (with Caching) ---
# Use st.cache_data to cache API responses
@st.cache_data
def get_departments():
    """Fetches the list of departments from the MET API."""
    try:
        response = requests.get("https://collectionapi.metmuseum.org/public/collection/v1/departments")
        response.raise_for_status() # Raise an error for bad responses
        data = response.json()
        return data.get("departments", [])
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
    search_url = "https://collectionapi.metmuseum.org/public/collection/v1/search"
    params = {
        'q': query,
        # --- FIX: Convert Python boolean to lowercase string "true" or None ---
        # The API expects the lowercase string "true", not the Python boolean True.
        'isHighlight': "true" if is_highlight else None, 
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
        st.error(f"Error searching API: {e}")
        return []
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        return []

@st.cache_data
def get_object_details(object_id):
    """Fetches the full details for a single object ID."""
    try:
        response = requests.get(f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{object_id}")
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        # Don't show an error for every failed object, just return None
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
st.sidebar.header("Search & Filter")

# 1. Load departments for the dropdown
departments = get_departments()
dept_names = ["All Departments"] + [dept['displayName'] for dept in departments]

# 2. Build a map of department name -> ID
# --- THIS IS THE FIXED LINE ---
dept_map = {dept['displayName']: dept['departmentId'] for dept in departments}
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
    st.info("Use the sidebar to search for artworks or click 'Surprise Me!' to get started.")
else:
    # --- Pagination Logic ---
    total_results = len(st.session_state.search_results)
    st.write(f"**Found {total_results} artworks.**")
    
    # Calculate start and end index for the current page
    start_idx = st.session_state.page * ITEMS_PER_PAGE
    end_idx = min(start_idx + ITEMS_PER_PAGE, total_results)
    ids_to_show = st.session_state.search_results[start_idx:end_idx]

    # --- Pagination Buttons ---
    page_col1, page_col2, page_col3 = st.columns([1, 1, 1])
    
    with page_col1:
        if st.session_state.page > 0:
            if st.button("⬅️ Previous Page"):
                st.session_state.page -= 1
                st.rerun()
                
    with page_col3:
        if end_idx < total_results:
            if st.button("Next Page ➡️"):
                st.session_state.page += 1
                st.rerun()
                
    st.divider()

    # --- Display Results ---
    # Fetch details and display them
    for object_id in ids_to_show:
        with st.spinner(f"Loading artwork {object_id}..."):
            details = get_object_details(object_id)
        
        if details:
            # Handle artworks with no public domain image
            if not details.get("primaryImageSmall"):
                st.write(f"**{details.get('title', 'Untitled')}** by {details.get('artistDisplayName', 'Unknown')}")
                st.warning("This artwork has no image available for display.")
                if details.get("objectURL"):
                    st.link_button("View on MET Website", details["objectURL"])
                st.divider()
                continue # Skip to the next artwork
            
            # Use columns for a clean layout: Image on left, text on right
            img_col, text_col = st.columns([1, 3])
            
            with img_col:
                st.image(
                    details.get("primaryImageSmall"),
                    caption=details.get("objectDate", ""),
                    use_column_width=True
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

