import time
import cloudscraper
import json
import discord_webhook

# Load configuration from JSON file
with open("config.json") as config_file:
    configuration = json.load(config_file)

# URL for making a purchase request
purchase_url = 'https://api.bloxpvp.com/marketplace/listing/purchase'

# Create a scraper instance
scraper = cloudscraper.create_scraper()

# Define custom headers to mimic a browser request
headers = {
    'Authorization': f"Bearer {configuration['token']}",
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/91.0.4472.124 Safari/537.36',
    'Referer': 'https://example.com',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Content-Type': 'application/json',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'TE': 'Trailers'
}

def get_username():
    try:
        response = scraper.get("https://api.bloxpvp.com/login-auto", headers=headers)
        return response.text
    except Exception as error:
        print(f"Failed to get username: {error}")
        return None

def fetch_listings():
    try:
        response = scraper.get("https://api.bloxpvp.com/marketplace/listings", headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to fetch listings: {response.status_code}")
            return None
    except Exception as error:
        print(f"Error fetching listings: {error}")
        return None

def purchase_item(entry):
    new_structure = {"chosenListings": [entry]}
    data = json.dumps(new_structure)
    try:
        response = scraper.post(purchase_url, data=data, headers=headers)
        return response.status_code, response.text
    except Exception as error:
        print(f"Error purchasing item: {error}")
        return None, str(error)

def snipe_items():
    client_user_name = get_username()
    if not client_user_name:
        return

    while True:
        print("Sniping for items...")
        operation_start_time = time.time()  # Start timing the entire operation

        try:
            form_data = fetch_listings()
            if not form_data:
                continue
        except Exception as error:
            discord_webhook.DiscordWebhook(
                url=configuration["web_hook_url"],
                content=f"Request failed, reason: {error}"
            ).execute()
            continue

        item_found = False
        for key, val in configuration['items'].items():
            for entry in form_data:
                item_name = entry["item"]["item"]["display_name"]
                item_rate = str(entry["rate"])
                item_value = entry["item"]["item"]["item_value"]
                item_image = entry["item"]["item"]["item_image"]
                game_name = entry["item"]["game"]
                item_owner = entry["posterUsername"]

                if item_name == val['item_name'] and item_rate == val["item_rate"] and item_owner != client_user_name:
                    item_found = True

                    status, response_text = purchase_item(entry)
                    print(response_text)

                    item_price = (float(item_value) / 1e3) * 5
                    formatted_price = f"{item_price:.2f}"

                    webhook = discord_webhook.DiscordWebhook(
                        url=configuration["web_hook_url"],
                        content="Bought item!",
                        rate_limit_retry=True
                    )

                    embed = discord_webhook.DiscordEmbed(
                        title=item_name,
                        description="||@everyone||",
                        color="03b2f8"
                    )

                    if scraper.get(item_image).status_code != 200:
                        item_image = "https://media.istockphoto.com/id/1472933890/vector/no-image-vector-symbol-missing-available-icon-no-gallery-for-this-moment-placeholder.jpg?s=612x612&w=0&k=20&c=Rdn-lecwAj8ciQEccm0Ep2RX50FCuUJOaEM8qQjiLL0="

                    embed.set_timestamp()
                    embed.set_image(url=item_image)
                    embed.set_footer(text=f"Rate: {item_rate}\nGame: {game_name}\nPrice: {formatted_price}")
                    webhook.add_embed(embed)

                    if status == 200:
                        print("Purchased item!")
                        webhook.execute()
                    else:
                        discord_webhook.DiscordWebhook(
                            url=configuration["web_hook_url"],
                            content=f"Error in buying. error: {response_text}"
                        ).execute()

        if not item_found:
            print("No matching item found.")

        operation_duration = time.time() - operation_start_time
        print(f"Total operation time: {operation_duration:.2f} seconds.")

# Run the sniping function
snipe_items()
