# museumapiexample
Using an open api for an app
🖼️ MET Artwork Explorer

This is a comprehensive web application built with Streamlit that allows users to perform deep, interactive searches and explore the entire public collection of The Metropolitan Museum of Art (MET).

It's designed to be a rich discovery tool, ensuring users never hit a dead end and can always find interesting art. The app uses the official MET Collection API.

🚀 Features

This app goes beyond a simple search bar and includes:

Multi-Filter Search: Combine filters to find exactly what you're looking for.

Keyword Search: Search by title, artist, or any other term.

Filter by Department: Narrow results to a specific curatorial department (e.g., "Arms and Armor," "Egyptian Art").

Filter by Year Range: Find artworks created within a specific time period (e.g., 1880-1890).

Filter by "Highlights": Show only the most popular and important artworks in the MET's collection.

Rich Exploration Tools:

"Surprise Me! 🎲" Button: Don't know what to search for? This button fetches a random, popular masterpiece.

"More from this Artist" Button: See an artwork you like? Click this button to see all other works by that artist.

Interactive Tag Buttons: Artworks are tagged with keywords (e.g., "Portraits," "Sunflowers," "Gold"). Click any tag to start a new search for that theme.

User-Friendly Interface:

Smart Fallback: If your specific search returns no results, the app automatically shows popular highlights instead, so you're never left with a blank page.

Rich Details: Results include all available info: artist bio, medium, dimensions, date, culture, and more.

Image Gallery: View the main image and any additional images (like different angles or close-ups) provided by the museum.

Pagination: Easily browse through thousands of results with "Next" and "Previous" page buttons.

Direct Link: A button links directly to the artwork's official page on the MET website.

Local Setup & Installation

Prerequisites

Python 3.8+

pip (Python package installer)

How to Run

Clone the GitHub repository:

git clone [https://github.com/YOUR-USERNAME/YOUR-REPO-NAME.git](https://github.com/YOUR-USERNAME/YOUR-REPO-NAME.git)
cd YOUR-REPO-NAME


Install the required dependencies:
This will install streamlit and requests.

pip install -r requirements.txt


Run the Streamlit app:

streamlit run app.py


The application will automatically open in your default web browser.
