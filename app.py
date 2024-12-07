from flask import Flask, render_template, request
import openai
import requests
from dotenv import load_dotenv
import os


# Load environment variables from .env
load_dotenv()

# Configure API keys
openai.api_key = os.getenv("OPENAI_API_KEY")
mapbox_api_key = os.getenv("MAPBOX_API_KEY")

app = Flask(__name__)


def translate_and_describe_food(chinese_food_name):
    """Uses OpenAI API to translate and provide detailed insights into Chinese cuisine."""
    try:
        # OpenAI API prompt using the new ChatCompletion structure
        messages = [
            {"role": "system", "content": "You are a culinary expert specializing in Chinese cuisine."},
            {"role": "user", "content": (
                f"Please provide a detailed description of the dish '{chinese_food_name}'. "
                f"Include the following details:\n"
                f"1. An English translation of the dish name.\n"
                f"2. Key ingredients.\n"
                f"3. Flavor profile (e.g., spicy, sweet, umami, etc.).\n"
                f"4. Regional origin within China (if applicable).\n"
                f"5. Cooking method (e.g., stir-fried, steamed, etc.).\n"
                f"6. A recommendation on whether the dish is suitable for foreigners trying Chinese food for the first time, and why."
            )}
        ]

        # Use the new ChatCompletion method with gpt-3.5-turbo
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  
            messages=messages, 
            max_tokens=300,  
            temperature=0.7 
        )

        # Extract content and format into structured data
        raw_content = response['choices'][0]['message']['content'].strip()
        description = [
            {"title": line.split(":")[0].strip(), "content": ":".join(line.split(":")[1:]).strip()}
            for line in raw_content.split("\n") if ":" in line
        ]
        return description
    except Exception as e:
        return [{"title": "Error", "content": str(e)}]


def generate_dish_image(chinese_food_name):
    """Uses OpenAI DALL·E API to generate a realistic image of the dish."""
    try:
        # Simplified prompt based only on the dish name
        prompt = f"A realistic photograph of the Chinese dish '{chinese_food_name}' served on a plate, with traditional Chinese tableware, in a natural setting."
        
        # Use OpenAI's DALL·E API to generate the image
        response = openai.Image.create(
            prompt=prompt,
            n=1,  
            size="512x512" 
        )

        # Return the URL of the generated image
        return response['data'][0]['url']
    except Exception as e:
        return None



def get_nearby_restaurants(zip_code):
    """Uses Mapbox API to find nearby Chinese restaurants."""
    try:
        # Geocode the zip code to get latitude and longitude
        geocode_url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{zip_code}.json?access_token={mapbox_api_key}"
        geo_response = requests.get(geocode_url).json()
        coordinates = geo_response['features'][0]['geometry']['coordinates']

        # Search for nearby Chinese restaurants
        search_url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/chinese restaurant.json?proximity={coordinates[0]},{coordinates[1]}&access_token={mapbox_api_key}"
        search_response = requests.get(search_url).json()
        
        restaurants = [place['place_name'] for place in search_response['features']]
        return restaurants if restaurants else ["No nearby Chinese restaurants found."]
    except Exception as e:
        return [f"Error: {e}"]


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        chinese_food_name = request.form["food_name"]
        zip_code = request.form.get("zip_code")

        # Get translation and description
        description = translate_and_describe_food(chinese_food_name)

        # Get nearby restaurants if zip code is provided
        restaurants = get_nearby_restaurants(zip_code) if zip_code else None

        # Generate image of the dish
        dish_image_url = generate_dish_image(chinese_food_name)

        return render_template(
            "result.html",
            food_name=chinese_food_name,
            description=description,
            restaurants=restaurants,
            dish_image_url=dish_image_url,
        )
    return render_template("index.html")



if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
