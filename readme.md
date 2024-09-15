
# Trakt.tv Watch History Widget
https://github.com/rudrakabir/Trakt-Embed
## Project Description

This project integrates a dynamic Trakt.tv watch history widget into a Jekyll-based website. It automatically fetches and displays the user's most recently watched TV show and movie from their Trakt.tv account, providing an up-to-date snapshot of their viewing activity.

### Key Features:

- **Real-time Updates**: Utilizes GitHub Actions to automatically fetch the latest watch data every 6 hours, ensuring the displayed information is always current.
- **Visual Appeal**: Includes poster images from The Movie Database (TMDb) alongside watch details, creating an visually engaging display.
- **Seamless Integration**: Designed to blend seamlessly with Jekyll-based websites, requiring minimal setup and maintenance.
- **Privacy-Aware**: Uses secure token authentication to access Trakt.tv data without storing sensitive information.
- **Customizable**: Easily adaptable CSS styling to match the look and feel of any website.

### Technical Highlights:

- Leverages the Trakt.tv API for fetching watch history data.
- Implements OAuth 2.0 flow with token refresh mechanism for secure, long-term API access.
- Uses GitHub Actions for automated, scheduled data updates.
- Generates static HTML that can be easily included in any Jekyll page or layout.

This widget offers a simple yet effective way to share your latest media consumption with your website visitors, adding a personal touch to your online presence.
