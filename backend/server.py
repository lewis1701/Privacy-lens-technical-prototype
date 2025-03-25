TRACKER_DATABASE = {
    "google-analytics": {"name": "Google Analytics", "category": "Analytics", "company": "Google"},
    "googletagmanager": {"name": "Google Tag Manager", "category": "Analytics", "company": "Google"},
    "doubleclick": {"name": "Google Ads", "category": "Advertising", "company": "Google"},
    "facebook": {"name": "Facebook Pixel", "category": "Advertising", "company": "Meta"},
    "ads-twitter": {"name": "Twitter Ads", "category": "Advertising", "company": "Twitter"},
    "tiktok": {"name": "TikTok Pixel", "category": "Advertising", "company": "TikTok"},
    "linkedin": {"name": "LinkedIn Insights", "category": "Social Media", "company": "LinkedIn"},
    "quantserve": {"name": "Quantcast", "category": "Advertising", "company": "Quantcast"},
    "scorecardresearch": {"name": "Scorecard Research", "category": "Analytics", "company": "ComScore"},
    "newrelic": {"name": "New Relic", "category": "Performance Monitoring", "company": "New Relic"},
    "mixpanel": {"name": "Mixpanel", "category": "Analytics", "company": "Mixpanel"},
    "hotjar": {"name": "Hotjar", "category": "User Behavior Analytics", "company": "Hotjar"},
    "youtube.com/pagead": {"name": "YouTube Ads", "category": "Advertising", "company": "Google"},
    "youtube.com/api/stats": {"name": "YouTube Analytics", "category": "Analytics", "company": "Google"},
}



from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "Flask server is running!"


@app.route('/scan', methods=['GET'])
def scan_website():
    """Scans a website for tracking scripts using Selenium and BeautifulSoup."""
    url = request.args.get("url")

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    # Ensure URL starts with http:// or https://
    if not url.startswith("http"):
        url = "https://" + url

    try:
        # Set up Selenium WebDriver (Headless Mode)
        options = Options()
        options.add_argument("--headless")
        service = Service(os.path.join(os.getcwd(), "backend", "chromedriver.exe"))
        driver = webdriver.Chrome(service=service, options=options)
        
        # Load the Website
        driver.get(url)
        page_source = driver.page_source
        driver.quit()

        # Analyze HTML with BeautifulSoup
        soup = BeautifulSoup(page_source, "html.parser")
        scripts = soup.find_all("script", src=True)

        # Debugging: Print all extracted script URLs
        print("\nExtracted Scripts:")
        extracted_scripts = [script['src'] for script in scripts]
        for script in extracted_scripts:
            print(script)


        # Detect trackers
        tracker_details = []
        for script in scripts:
            tracker_url = script['src']
            for known_url, details in TRACKER_DATABASE.items():
                if known_url in tracker_url:
                    tracker_details.append({
                        "url": tracker_url,
                        "name": details["name"],
                        "category": details["category"],
                        "company": details["company"]
                    })
                    break  # Stop checking once a match is found

        # Calculate Privacy Score
        privacy_score = max(0, 100 - len(tracker_details) * 10)

        return jsonify({
            "url": url,
            "trackers": tracker_details,
            "privacy_score": privacy_score
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print("Starting Flask server...")
    app.run(debug=True)
