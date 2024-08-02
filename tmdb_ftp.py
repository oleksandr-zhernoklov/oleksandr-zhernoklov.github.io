import os
import re
import csv
import requests
import pandas as pd
from datetime import datetime
from jinja2 import Template
import ftplib

# Function to map genre id to value
def get_genre_value(genre_id):
    genre_mapping = {
        28: 'Action',
        12: 'Adventure',
        16: 'Animation',
        35: 'Comedy',
        80: 'Crime',
        99: 'Documentary',
        18: 'Drama',
        10751: 'Family',
        14: 'Fantasy',
        36: 'History',
        27: 'Horror',
        10402: 'Music',
        9648: 'Mystery',
        10749: 'Romance',
        878: 'Science Fiction',
        10770: 'TV Movie',
        53: 'Thriller',
        10752: 'War',
        37: 'Western'
    }
    return genre_mapping.get(genre_id, 'Unknown')

# Function to generate HTML table
def generate_html_table(successful_results):
    # Load the HTML template
    template_str = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Movie Results</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/jquery.tablesorter/2.31.3/css/theme.default.min.css">
        <script src="https://code.jquery.com/jquery-3.6.4.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery.tablesorter/2.31.3/js/jquery.tablesorter.min.js"></script>
        <style>
            .checkbox-column {
                text-align: center;
            }
            .poster-column img {
                width: 100px;
                height: auto;
            }
        </style>
    </head>
    <body>
    
    <h2>Successful Results</h2>
    
    <div class="links">
        <a href="downloaded.html" target="_self">View Downloaded Page</a>
    </div>
    
    <table id="movieTable" class="tablesorter">
        <thead>
            <tr>
                <th>File</th>
                <th>File Size (GB)</th>
                <th>Title</th>
                <th>Genre</th>
                <th>TMDB ID</th>
                <th>Year</th>
                <th>Length (minutes)</th>
                <th>TMDB Link</th>
                <th>Description</th>
                <th>Rating</th>
                <th class="checkbox-column">Easy</th>
                <th class="checkbox-column">Heavy</th>
                <th>Toloka Link</th>
                <th>Rutracker Link</th>
                <th>Poster</th>
                <th>Trailer</th>
            </tr>
        </thead>
        <tbody>
            {% for result in successful_results %}
                <tr>
                    <td>{{ result['File'] }}</td>
                    <td>{{ result['File_gb'] }}</td>
                    <td>{{ result['Title'] }}</td>
                    <td>{{ result['Genre']|join(', ') }}</td>
                    <td>{{ result['TMDB ID'] }}</td>
                    <td>{{ result['Year'] }}</td>
                    <td>{{ result['Length'] }}</td>
                    <td><a href="{{ result['TMDB Link'] }}" target="_blank">{{ result['TMDB Link'] }}</a></td>
                    <td>{{ result['Description'] }}</td>
                    <td>{{ result['Rating'] }}</td>
                    <td class="checkbox-column"><input type="checkbox" class="easy-checkbox" data-file="{{ result['File'] }}"></td>
                    <td class="checkbox-column"><input type="checkbox" class="heavy-checkbox" data-file="{{ result['File'] }}"></td>
                    <td><a href="https://toloka.to/tracker.php?nm={{ result['Title'] }}" target="_blank">Toloka</a></td>
                    <td><a href="https://rutracker.org/forum/tracker.php?nm={{ result['Title'] }}" target="_blank">Rutracker</a></td>
                    <td class="poster-column"><img src="{{ result['Poster'] }}" alt="Poster"></td>
                    <td><a href="{{ result['Trailer'] }}" target="_blank">Trailer</a></td>
                </tr>
            {% endfor %}
        </tbody>
    </table>
    
    <script>
        $(document).ready(function(){
            // Initialize tablesorter
            $("#movieTable").tablesorter();

            // Save checkbox values to localStorage
            function saveCheckboxValues() {
                var easyValues = {};
                var heavyValues = {};

                $(".easy-checkbox").each(function() {
                    var file = $(this).data("file");
                    easyValues[file] = $(this).is(":checked");
                });

                $(".heavy-checkbox").each(function() {
                    var file = $(this).data("file");
                    heavyValues[file] = $(this).is(":checked");
                });

                localStorage.setItem("easyValues", JSON.stringify(easyValues));
                localStorage.setItem("heavyValues", JSON.stringify(heavyValues));
            }

            // Load checkbox values from localStorage
            function loadCheckboxValues() {
                var easyValues = JSON.parse(localStorage.getItem("easyValues") || "{}");
                var heavyValues = JSON.parse(localStorage.getItem("heavyValues") || "{}");

                $(".easy-checkbox").each(function() {
                    var file = $(this).data("file");
                    $(this).prop("checked", easyValues[file] || false);
                });

                $(".heavy-checkbox").each(function() {
                    var file = $(this).data("file");
                    $(this).prop("checked", heavyValues[file] || false);
                });
            }

            // Save checkbox values on change
            $(".easy-checkbox, .heavy-checkbox").on("change", saveCheckboxValues);

            // Load checkbox values on page load
            loadCheckboxValues();
        });
    </script>
    
    </body>
    </html>
    """
    template = Template(template_str)

    # Render the template with the successful_results data
    rendered_html = template.render(successful_results=successful_results)

    # Save the rendered HTML to a file
    with open('movie_results.html', 'w', encoding='utf-8') as html_file:
        html_file.write(rendered_html)

    print('HTML file generated successfully: movie_results.html')

# Function to get file size from FTP server
def get_ftp_file_size(ftp, filename):
    try:
        # Use the FTP 'size' command to get the file size
        size = ftp.size(filename)
        return size
    except ftplib.error_perm as e:
        print(f"Could not get size for file {filename}: {e}")
        return None

# Function to get FTP file listing and sizes
def get_ftp_listing(host, user, password, working_dir='2tb/Download2/Movies'):
    try:
        ftp = ftplib.FTP(host, user, password)
        if working_dir:
            ftp.cwd(working_dir)
        file_listing = ftp.nlst()
        file_sizes = {}

        for filename in file_listing:
            size = get_ftp_file_size(ftp, filename)
            if size is not None:
                file_sizes[filename] = round(size / (1024 * 1024 * 1024), 2)  # Convert bytes to GB

        ftp.quit()
        return file_listing, file_sizes
    except Exception as e:
        print(f"An error occurred: {type(e).__name__}, {str(e)}")
        return [], {}

# Function to process video files from multiple directories
def process_video_files(directories, tmdb_api_key, ftp_details=None):
    video_files = []
    ftp_file_sizes = {}

    # Process local directories
    for directory in directories:
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.lower().endswith(('.mp4', '.avi', '.mkv')):
                    video_files.append(os.path.join(root, file))
    
    # Process FTP directory if details are provided
    if ftp_details:
        ftp_files, ftp_file_sizes = get_ftp_listing(ftp_details['host'], ftp_details['user'], ftp_details['pass'], ftp_details['path'])
        for file in ftp_files:
            if file.lower().endswith(('.mp4', '.avi', '.mkv')):
                video_files.append(file)

    # Lists to store successful and failed results
    successful_results = []
    failed_results = []

    # TMDB API request
    for file in video_files:
        # Extract the filename without extension
        filename = os.path.splitext(os.path.basename(file))[0]
        file_gb = round(os.path.getsize(file) / (1024 * 1024 * 1024), 2) if os.path.exists(file) else 'N/A'

        # If file is from FTP, use the FTP file size
        if file in ftp_file_sizes:
            file_gb = ftp_file_sizes[file]

        # Remove year from filename (inside brackets or after dot)
        filename_without_year = re.sub(r"\(\d{4}\)|\.\d{4}(?=\D|$)", "", filename).strip()
        # Extract only the movie name
        pattern = r"^(.*?)\s\(\d{4}\)"
        match = re.match(pattern, filename)
        if match:
            movie_name = match.group(1)
            print(match.group(1))
        else:
            # No movie found
            failed_results.append({'File': file, 'Result': 'No regexp'})
            continue

        # Make a request to TMDB API to search for the movie
        url = f"https://api.themoviedb.org/3/search/movie?api_key={tmdb_api_key}&query={movie_name}"
        response = requests.get(url)

        if response.status_code == 200:
            # Request successful
            data = response.json()
            if data['results']:
                # Get the first movie result
                movie = data['results'][0]

                # Extract relevant information from the response
                movie_title = movie['title']
                movie_genre_ids = movie['genre_ids']
                movie_id = movie['id']
                if movie['release_date'] and movie['release_date'] != 'N/A':
                    try:
                        movie_year = datetime.strptime(movie['release_date'], '%Y-%m-%d').year
                    except ValueError:
                        # Handle the case where the date format is incorrect
                        movie_year = None
                    else:
                        movie_year = None

                # Map genre ids to corresponding values
                genre_values = [get_genre_value(genre_id) for genre_id in movie_genre_ids]

                # Get movie details
                details_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={tmdb_api_key}&append_to_response=videos"
                details_response = requests.get(details_url)
                details_data = details_response.json()

                movie_length = details_data.get('runtime', 'N/A')
                movie_rating = details_data.get('vote_average', 'N/A')
                movie_description = details_data.get('overview', 'N/A')
                movie_poster = f"https://image.tmdb.org/t/p/w200{details_data.get('poster_path', '')}"
                tmdb_link = f"https://www.themoviedb.org/movie/{movie_id}"
                
                # Extract trailer information
                videos_data = details_data.get('videos', {})
                trailer = next((video for video in videos_data.get('results', []) if video['type'] == 'Trailer'), None)
                trailer_link = f"https://www.youtube.com/watch?v={trailer['key']}" if trailer else 'N/A'

                # Store successful result
                successful_results.append({
                    'File': file.replace(",", ""),
                    'File_gb': file_gb,
                    'Title': movie_title,
                    'Genre': genre_values,
                    'TMDB ID': movie_id,
                    'Year': movie_year,
                    'Length': movie_length,
                    'TMDB Link': tmdb_link,
                    'Description': movie_description,
                    'Rating': movie_rating,
                    'Toloka Link': f"https://toloka.to/tracker.php?nm={movie_title}",
                    'Rutracker Link': f"https://rutracker.org/forum/tracker.php?nm={movie_title}",
                    'Poster': movie_poster,
                    'Trailer': trailer_link
                })
            else:
                # No movie found
                failed_results.append({'File': file, 'Result': 'No movie found'})
        else:
            # Request failed
            failed_results.append({'File': file, 'Result': 'Failed to retrieve movie information'})

    successful_results = sorted(successful_results, key=lambda x: x.get('Year') or '')
    return successful_results, failed_results

def save_results_to_csv_and_excel(successful_results, failed_results):
    # Save successful results to CSV file
    successful_csv_path = 'successful_results.csv'
    successful_fields = ['File', 'File_gb', 'Title', 'Genre', 'TMDB ID', 'Year', 'Length', 'TMDB Link', 'Description', 'Rating', 'Toloka Link', 'Rutracker Link', 'Poster', 'Trailer']

    with open(successful_csv_path, 'w', newline='', encoding='utf-8') as successful_file:
        writer = csv.DictWriter(successful_file, fieldnames=successful_fields)
        writer.writeheader()
        writer.writerows(successful_results)

    print(f'Successful results saved to: {successful_csv_path}')

    # Save successful results to Excel file
    successful_excel_path = 'successful_results.xlsx'

    df = pd.DataFrame(successful_results)
    df.to_excel(successful_excel_path, index=False, engine='openpyxl')

    print(f'Successful results saved to: {successful_excel_path}')

    # Save failed results to CSV file
    failed_csv_path = 'failed_results.csv'
    failed_fields = ['File', 'Result']

    with open(failed_csv_path, 'w', newline='', encoding='utf-8') as failed_file:
        writer = csv.DictWriter(failed_file, fieldnames=failed_fields)
        writer.writeheader()
        writer.writerows(failed_results)

    print(f'Failed results saved to: {failed_csv_path}')

# Main function
def main():
    # List of directories to process
    directories = [
        r'G:/Movies'
        # Add more directories as needed
    ]

    # FTP details
    ftp_details = {
        'host': '45.152.75.187',
        'user': 'saf',
        'pass': 'iMV9vDHFM@9Drvb',
        'path': '2tb/Download2/Movies'
    }

    # TMDB API key
    tmdb_api_key = 'fb70d4fb95572e0ddd9bc99f90734e46'

    # Process video files and get results
    successful_results, failed_results = process_video_files(directories, tmdb_api_key, ftp_details)

    # Save results to CSV and Excel files
    #save_results_to_csv_and_excel(successful_results, failed_results)

    # Generate HTML table
    generate_html_table(successful_results)

if __name__ == "__main__":
    main()
