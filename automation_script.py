import asyncio
import json
from playwright.async_api import async_playwright
import httpx

# Step 1: Save session after the initial manual login
async def save_session():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Use Chromium
        context = await browser.new_context()

        # Open the login page
        page = await context.new_page()
        await page.goto("https://suno.com/login")

        print("Please log in manually via the browser window.")
        print("Once logged in, close the browser window to save the session.")

        # Wait for manual login
        await page.wait_for_timeout(60000)  # Wait 60 seconds for manual login

        # Save storage state (cookies + local storage) to a file
        await context.storage_state(path="auth.json")
        print("Session saved successfully to auth.json.")
        await browser.close()

# Step 2: Automatically restore session and log in
async def restore_session_and_login():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Use Chromium
        # Load the saved session
        try:
            context = await browser.new_context(storage_state="auth.json")
        except Exception as e:
            print("Error loading session data:", e)
            return

        # Open the login page
        page = await context.new_page()
        await page.goto("https://suno.com/login")

        # Check if login is successful
        await page.wait_for_timeout(5000)  # Wait a few seconds for the page to load
        if "dashboard" in page.url:  # Adjust "dashboard" based on your application's post-login URL
            print("Logged in successfully using the saved session!")
        else:
            print("Automatic login failed. Please check your session data.")
            return

        # Navigate to the song generation page or API
        print("Navigating to the song generation page...")
        await page.goto("https://suno.com/song/generate")  # Replace with the actual URL

        # Optional: Extract some UI element text as confirmation
        heading = await page.text_content("h1")  # Example selector
        print(f"Page heading: {heading}")

        # Perform a song generation request via API
        await generate_song_request()

        # Close the browser
        await browser.close()

# Step 3: Perform a song generation request via API
async def generate_song_request():
    print("Performing song generation request via API...")
    async with httpx.AsyncClient() as client:
        # Load cookies from the saved session
        try:
            with open("auth.json", "r") as f:
                session_data = json.load(f)
        except FileNotFoundError:
            print("auth.json not found. Please save the session first.")
            return

        cookies = {c['name']: c['value'] for c in session_data.get('cookies', [])}

        # Define the API request payload
        url = "https://suno.com/api/song/generate"
        payload = {
            "song_name": "My Test Song",
            "artist": "Test Artist",
            "genre": "Pop"
        }

        # Make the API request with cookies
        response = await client.post(url, json=payload, cookies=cookies)
        if response.status_code == 200:
            response_data = response.json()
            song_uuid = response_data.get("song_uuid")
            print(f"Song generation requested successfully. UUID: {song_uuid}")
            await check_song_status(song_uuid)
        else:
            print(f"Failed to generate song. Response: {response.text}")

# Step 4: Check song generation status
async def check_song_status(song_uuid):
    print("Checking song generation status...")
    async with httpx.AsyncClient() as client:
        # Load cookies from the saved session
        try:
            with open("auth.json", "r") as f:
                session_data = json.load(f)
        except FileNotFoundError:
            print("auth.json not found. Please save the session first.")
            return

        cookies = {c['name']: c['value'] for c in session_data.get('cookies', [])}

        # Poll the status API
        url = f"https://suno.com/api/song/status/{song_uuid}"
        while True:
            response = await client.get(url, cookies=cookies)
            if response.status_code == 200:
                response_data = response.json()
                status = response_data.get("status")

                print(f"Song status: {status}")

                if status == "completed":
                    print("Song generation completed!")
                    break
                elif status == "failed":
                    print("Song generation failed.")
                    break
            else:
                print(f"Error checking song status: {response.text}")
                break

            await asyncio.sleep(5)  # Wait 5 seconds before checking again

# Main function to coordinate workflow
async def main():
    # Uncomment the following line to save session manually the first time:
    # await save_session()

    print("Step 1: Restore session and log in automatically")
    await restore_session_and_login()

# Run the script
asyncio.run(main())
