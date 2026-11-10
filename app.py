import streamlit as st
from PIL import Image, ImageOps
from google import genai
from google.genai import types
import requests
import io
import json
import re
import hashlib
import time

# =====================================================
# 1. PAGE CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="IMAGEAI | Smart Image Tag Generator",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =====================================================
# 2. SESSION STATE
# =====================================================

if "image_results" not in st.session_state:
    st.session_state.image_results = {}

if "url_image_bytes" not in st.session_state:
    st.session_state.url_image_bytes = None

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

# =====================================================
# 3. DARK MODE
# =====================================================

with st.sidebar:
    st.markdown("### ⚙️ Appearance")
    st.session_state.dark_mode = st.toggle(
        "🌙 Dark Mode",
        value=st.session_state.dark_mode
    )

if st.session_state.dark_mode:
    background = "#111827"
    text_color = "#F9FAFB"
    heading_color = "#D8CCFF"
    card_background = "#1F2937"
    caption_color = "#D1D5DB"
else:
    background = "#F5F6FC"
    text_color = "#25233A"
    heading_color = "#302B78"
    card_background = "#FFFFFF"
    caption_color = "#77758C"

# =====================================================
# 4. CUSTOM CSS
# =====================================================

st.markdown(f"""
<style>
.stApp {{
    background-color: {background};
    color: {text_color};
}}

.block-container {{
    max-width: 1200px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}}

h1, h2, h3, h4 {{
    color: {heading_color};
}}

p, label {{
    color: {text_color};
}}

div.stButton > button {{
    background: linear-gradient(90deg, #6044C7, #9462DF);
    color: white;
    border: none;
    border-radius: 11px;
    min-height: 46px;
    font-weight: 650;
}}

div.stButton > button:hover {{
    color: white;
    border: 1px solid #6044C7;
}}

div[data-testid="stFileUploader"] {{
    background: {card_background};
    border: 2px dashed #A99AE5;
    border-radius: 14px;
    padding: 15px;
}}

div[data-testid="stVerticalBlockBorderWrapper"] {{
    background: {card_background};
    border-radius: 12px;
}}

div[data-testid="stAlert"] {{
    border-radius: 12px;
}}
</style>
""", unsafe_allow_html=True)

# =====================================================
# 5. IMAGEAI HEADER - HTML INDENTATION FIXED
# =====================================================

st.markdown("""
<div style="background:linear-gradient(120deg,#302B78,#6246C7,#9361DB);padding:42px 38px;border-radius:22px;margin-bottom:25px;">
<div style="color:#E6DFFF;font-size:13px;letter-spacing:2px;font-weight:700;">AI POWERED IMAGE INTELLIGENCE</div>
<div style="font-size:48px;font-weight:800;color:white;margin-top:8px;margin-bottom:8px;">✨ IMAGEAI</div>
<div style="color:white;font-size:25px;font-weight:650;margin-bottom:12px;">Turn Images Into Meaningful Tags</div>
<div style="color:#F0EBFF;font-size:17px;line-height:1.7;">Upload an image. Let artificial intelligence understand its contents and organize the results into meaningful descriptive categories.</div>
</div>
""", unsafe_allow_html=True)

# =====================================================
# 6. FEATURE CARDS
# =====================================================

st.subheader("Explore IMAGEAI")

c1, c2, c3 = st.columns(3)

with c1:
    with st.container(border=True):
        st.markdown("## 📤")
        st.markdown("**Easy Image Upload**")
        st.caption(
            "Upload images directly from your computer "
            "or through an image URL."
        )

with c2:
    with st.container(border=True):
        st.markdown("## 🤖")
        st.markdown("**Intelligent AI Analysis**")
        st.caption(
            "Gemini AI identifies visible objects, people, "
            "colors and surroundings."
        )

with c3:
    with st.container(border=True):
        st.markdown("## 🏷️")
        st.markdown("**Structured Smart Tags**")
        st.caption(
            "Automatically organizes image tags into "
            "meaningful categories."
        )

st.divider()

# =====================================================
# 7. IMAGE PROCESSING
# =====================================================

def process_image(image_data):
    if not image_data:
        raise ValueError("The image is empty.")

    try:
        image = Image.open(io.BytesIO(image_data))
        image = ImageOps.exif_transpose(image)
        image = image.convert("RGB")
        image.thumbnail((1800, 1800))

        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=90)

        return image, buffer.getvalue()

    except Exception as exc:
        raise ValueError(
            "Invalid image. Upload a valid JPG, PNG or WebP file."
        ) from exc


def get_image_id(image_bytes):
    return hashlib.sha256(image_bytes).hexdigest()


# =====================================================
# 8. TAG CATEGORIES AND EMOJIS
# =====================================================

CATEGORY_EMOJIS = {
    "People": "👥",
    "Animals": "🐾",
    "Objects": "📦",
    "Nature": "🌿",
    "Colors": "🎨",
    "Clothing": "👗",
    "Food": "🍽️",
    "Buildings": "🏢",
    "Activities": "🎯",
    "Scene & Setting": "🌍",
    "Other": "🔖"
}

VALID_CATEGORIES = list(CATEGORY_EMOJIS.keys())

EMOJI_MAPPING = {
    "woman": "👩",
    "man": "👨",
    "person": "🧍",
    "people": "👥",
    "dog": "🐶",
    "cat": "🐱",
    "bird": "🐦",
    "horse": "🐴",
    "elephant": "🐘",
    "animal": "🐾",
    "flower": "🌸",
    "rose": "🌹",
    "tree": "🌳",
    "plant": "🪴",
    "nature": "🌿",
    "mountain": "⛰️",
    "beach": "🏖️",
    "ocean": "🌊",
    "sky": "🌤️",
    "sun": "☀️",
    "car": "🚗",
    "bike": "🏍️",
    "bus": "🚌",
    "train": "🚆",
    "airplane": "✈️",
    "apple": "🍎",
    "banana": "🍌",
    "food": "🍽️",
    "pizza": "🍕",
    "cake": "🎂",
    "building": "🏢",
    "house": "🏠",
    "office": "🏢",
    "dress": "👗",
    "saree": "🥻",
    "shirt": "👕",
    "clothing": "👕",
    "shoes": "👟",
    "bag": "👜",
    "book": "📚",
    "laptop": "💻",
    "computer": "🖥️",
    "phone": "📱",
    "camera": "📷",
    "music": "🎵",
    "football": "⚽",
    "cricket": "🏏",
    "wedding": "💍",
    "birthday": "🎂",
    "travel": "✈️",
    "red": "🔴",
    "blue": "🔵",
    "green": "🟢",
    "yellow": "🟡",
    "black": "⚫",
    "white": "⚪",
    "purple": "🟣",
    "pink": "🩷",
    "brown": "🟤"
}


def get_matching_emoji(tag, ai_emoji=""):
    tag_lower = tag.lower()

    for keyword, emoji in EMOJI_MAPPING.items():
        if re.search(r"\b" + re.escape(keyword) + r"\b", tag_lower):
            return emoji

    return ai_emoji if ai_emoji else "🔖"


def normalize_category(category):
    category = str(category).strip().lower()

    category_map = {
        "person": "People",
        "human": "People",
        "animal": "Animals",
        "vehicle": "Objects",
        "technology": "Objects",
        "plants": "Nature",
        "landscape": "Nature",
        "color": "Colors",
        "colour": "Colors",
        "fashion": "Clothing",
        "dress": "Clothing",
        "architecture": "Buildings",
        "building": "Buildings",
        "activity": "Activities",
        "sports": "Activities",
        "background": "Scene & Setting",
        "setting": "Scene & Setting",
        "scene": "Scene & Setting"
    }

    for valid in VALID_CATEGORIES:
        if category == valid.lower():
            return valid

    return category_map.get(category, "Other")


# =====================================================
# 9. GEMINI AI IMAGE ANALYSIS
# =====================================================

def generate_ai_analysis(image_bytes):
    api_key = st.secrets.get("GEMINI_API_KEY", "")
    model_name = st.secrets.get(
        "GEMINI_MODEL",
        "gemini-3.6-flash"
    )

    if not api_key:
        raise ValueError(
            "Gemini API key is missing. Check secrets.toml."
        )

    client = genai.Client(api_key=api_key)

    prompt = """
Analyze the uploaded image carefully.

Return ONLY valid JSON in this format:

{
    "caption": "A short factual sentence describing the image",
    "image_category": "One overall category",
    "tags": [
        {
            "category": "People",
            "tag": "Woman",
            "emoji": "👩"
        },
        {
            "category": "Clothing",
            "tag": "Purple Saree",
            "emoji": "🥻"
        }
    ]
}

Allowed categories:
People, Animals, Objects, Nature, Colors, Clothing,
Food, Buildings, Activities, Scene & Setting, Other.

Instructions:
1. Generate 8 to 12 accurate tags when possible.
2. Generate a meaningful image caption.
3. Identify the overall image category.
4. Identify only things visible in the image.
5. Avoid duplicate tags.
6. Use appropriate emojis.
7. Use short descriptive tag names.
8. Do not guess a person's identity.
9. Return valid JSON only.
"""

    for attempt in range(3):
        try:
            with st.spinner("🤖 Gemini AI is analyzing your image..."):
                response = client.models.generate_content(
                    model=model_name,
                    contents=[
                        types.Part.from_bytes(
                            data=image_bytes,
                            mime_type="image/jpeg"
                        ),
                        prompt
                    ],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.2
                    )
                )

            if not response.text:
                raise ValueError("Gemini returned an empty response.")

            return response.text

        except Exception as exc:
            error_message = str(exc).upper()

            if "429" in error_message or "RESOURCE_EXHAUSTED" in error_message:
                raise RuntimeError(
                    "Gemini API quota or rate limit reached. "
                    "Check your Google AI Studio usage."
                ) from exc

            temporary_error = any(
                code in error_message
                for code in [
                    "503", "UNAVAILABLE", "500",
                    "504", "DEADLINE_EXCEEDED"
                ]
            )

            if temporary_error and attempt < 2:
                wait_time = 2 ** (attempt + 1)
                st.warning(
                    f"Gemini is temporarily busy. Retrying in {wait_time} seconds."
                )
                time.sleep(wait_time)
                continue

            if "404" in error_message or "NOT_FOUND" in error_message:
                raise RuntimeError(
                    f"Model '{model_name}' is unavailable. "
                    "Check the model name and API access."
                ) from exc

            raise RuntimeError(
                f"Gemini analysis failed: {exc}"
            ) from exc

    raise RuntimeError("Unable to analyze the image. Please try again.")


# =====================================================
# 10. PARSE GEMINI RESPONSE
# =====================================================

def extract_analysis(response_text):
    text = response_text.strip()

    text = re.sub(
        r"^```(?:json)?\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(r"\s*```$", "", text)

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        raise ValueError("Gemini did not return valid JSON.")

    data = json.loads(text[start:end + 1])

    results = []
    seen = set()

    for item in data.get("tags", []):
        if not isinstance(item, dict):
            continue

        tag = str(item.get("tag", "")).strip()

        if not tag or tag.lower() in seen:
            continue

        seen.add(tag.lower())

        category = normalize_category(
            item.get("category", "Other")
        )

        emoji = get_matching_emoji(
            tag,
            str(item.get("emoji", "")).strip()
        )

        results.append({
            "category": category,
            "tag": tag,
            "emoji": emoji
        })

    return {
        "caption": str(
            data.get("caption", "No caption available.")
        ).strip(),
        "image_category": str(
            data.get("image_category", "Uncategorized")
        ).strip(),
        "tags": results
    }


# =====================================================
# 11. IMAGE UPLOAD
# =====================================================

st.header("📸 Upload Your Image")
st.caption("Choose how you want to provide your image.")

upload_method = st.radio(
    "Image source",
    ["Upload from Computer", "Upload using Image URL"],
    horizontal=True
)

image_inputs = []

# =====================================================
# 12. MULTIPLE IMAGE UPLOAD
# =====================================================

if upload_method == "Upload from Computer":

    uploaded_files = st.file_uploader(
        "Drag and drop or browse your images",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True,
        help="Maximum file size: 5 MB per image",
        key="computer_images"
    )

    if uploaded_files:
        for uploaded_file in uploaded_files:
            if uploaded_file.size > 5 * 1024 * 1024:
                st.error(
                    f"{uploaded_file.name} is larger than 5 MB."
                )
            else:
                image_inputs.append((
                    uploaded_file.name,
                    uploaded_file.getvalue()
                ))

    st.session_state.url_image_bytes = None

# =====================================================
# 13. IMAGE URL UPLOAD - SUPPORTS WEBP
# =====================================================

else:

    image_url = st.text_input(
        "Paste direct image URL",
        placeholder="https://example.com/image.jpg"
    )

    if st.button("🔍 Load Image", use_container_width=True):
        try:
            if not image_url.startswith(("https://", "http://")):
                raise ValueError(
                    "Please enter a valid HTTP or HTTPS URL."
                )

            response = requests.get(image_url, timeout=20)
            response.raise_for_status()

            if len(response.content) > 5 * 1024 * 1024:
                raise ValueError("Image must be smaller than 5 MB.")

            # Pillow checks the actual image format.
            # JPG, PNG and WebP are accepted.

            _, corrected_bytes = process_image(response.content)

            st.session_state.url_image_bytes = corrected_bytes

            st.success("Image loaded successfully!")

        except requests.exceptions.Timeout:
            st.error("The image URL took too long to respond.")

        except requests.exceptions.RequestException as exc:
            st.error(f"Could not download the image: {exc}")

        except Exception as exc:
            st.error(f"Image upload error: {exc}")

    if st.session_state.url_image_bytes:
        image_inputs.append((
            "image_from_url.jpg",
            st.session_state.url_image_bytes
        ))


# =====================================================
# 14. IMAGE PREVIEW AND AI GENERATION
# =====================================================

if image_inputs:

    st.caption(f"{len(image_inputs)} image(s) selected.")

    for image_index, (filename, original_bytes) in enumerate(image_inputs):

        try:
            image, corrected_bytes = process_image(original_bytes)
            image_id = get_image_id(corrected_bytes)

            st.divider()
            st.header(f"🖼️ Image Preview {image_index + 1}")

            left, right = st.columns([1.15, 0.85], gap="large")

            with left:
                with st.container(border=True):
                    st.image(
                        image,
                        caption=filename,
                        use_container_width=True
                    )

            with right:
                with st.container(border=True):
                    st.subheader("✨ Ready for AI Analysis")
                    st.write(
                        "Your image is loaded and validated. "
                        "Click below to identify and organize "
                        "the image contents."
                    )

                    st.success("Image received")
                    st.success("Image validated")
                    st.success("Orientation corrected")
                    st.success("Ready for AI analysis")

                    generate = st.button(
                        "✨ Generate Structured Tags",
                        use_container_width=True,
                        key=f"generate_{image_id}"
                    )

            # Generate AI results

            if generate:
                try:
                    response_text = generate_ai_analysis(corrected_bytes)
                    analysis = extract_analysis(response_text)

                    if not analysis["tags"]:
                        st.warning(
                            "No tags were generated. Please try again."
                        )
                    else:
                        st.session_state.image_results[image_id] = {
                            "filename": filename,
                            "caption": analysis["caption"],
                            "image_category": analysis["image_category"],
                            "tags": analysis["tags"]
                        }

                        st.success(
                            f"Successfully generated {len(analysis['tags'])} tags!"
                        )

                except Exception as exc:
                    st.error(f"AI analysis failed: {exc}")

            # Display results

            if image_id in st.session_state.image_results:

                result = st.session_state.image_results[image_id]
                tags = result["tags"]

                st.divider()
                st.header("🏷️ AI Generated Tags")

                st.caption(
                    "Your image tags are automatically grouped "
                    "into meaningful categories."
                )

                # Image caption

                st.subheader("📝 Image Caption")
                st.info(result["caption"])

                # Image category

                st.subheader("🗂️ Image Category")
                st.success(result["image_category"])

                # Metrics

                categories = set(
                    item["category"] for item in tags
                )

                metric1, metric2, metric3 = st.columns(3)

                metric1.metric("Total Tags", len(tags))
                metric2.metric("Categories", len(categories))
                metric3.metric("AI Analysis", "Complete")

                st.divider()

                # =================================================
                # 15. TAG SEARCH
                # =================================================

                st.subheader("🔎 Search Tags")

                search_text = st.text_input(
                    "Search for a tag",
                    placeholder="Type a keyword to search...",
                    key=f"search_{image_id}"
                )

                filtered_tags = [
                    item for item in tags
                    if search_text.lower() in item["tag"].lower()
                ]

                if search_text:
                    st.caption(
                        f"Found {len(filtered_tags)} matching tag(s)."
                    )

                # =================================================
                # 16. TAG EDITING AND DELETION
                # =================================================

                st.subheader("✏️ Edit Your Tags")

                for tag_index, item in enumerate(tags):

                    with st.expander(
                        f"{item['emoji']} {item['tag']} - {item['category']}"
                    ):

                        edited_tag = st.text_input(
                            "Tag name",
                            value=item["tag"],
                            key=f"edit_tag_{image_id}_{tag_index}"
                        )

                        category_index = VALID_CATEGORIES.index(
                            item["category"]
                        )

                        edited_category = st.selectbox(
                            "Tag category",
                            VALID_CATEGORIES,
                            index=category_index,
                            key=f"edit_category_{image_id}_{tag_index}"
                        )

                        edit_col1, edit_col2 = st.columns(2)

                        with edit_col1:
                            if st.button(
                                "Save Changes",
                                key=f"save_{image_id}_{tag_index}"
                            ):
                                if not edited_tag.strip():
                                    st.warning("Tag name cannot be empty.")
                                else:
                                    duplicate = any(
                                        other_index != tag_index
                                        and other["tag"].lower()
                                        == edited_tag.strip().lower()
                                        for other_index, other in enumerate(tags)
                                    )

                                    if duplicate:
                                        st.warning("This tag already exists.")
                                    else:
                                        item["tag"] = edited_tag.strip()
                                        item["category"] = edited_category
                                        item["emoji"] = get_matching_emoji(
                                            edited_tag,
                                            CATEGORY_EMOJIS[edited_category]
                                        )
                                        st.rerun()

                        with edit_col2:
                            if st.button(
                                "Delete Tag",
                                key=f"delete_{image_id}_{tag_index}"
                            ):
                                tags.pop(tag_index)
                                st.rerun()

                # =================================================
                # 17. DISPLAY TAGS BY CATEGORY
                # =================================================

                st.divider()
                st.subheader("📋 Generated Image Tags")

                for category in VALID_CATEGORIES:

                    category_tags = [
                        item for item in filtered_tags
                        if item["category"] == category
                    ]

                    if not category_tags:
                        continue

                    st.subheader(
                        f"{CATEGORY_EMOJIS[category]} {category}"
                    )

                    tag_columns = st.columns(3)

                    for tag_index, item in enumerate(category_tags):

                        with tag_columns[tag_index % 3]:
                            with st.container(border=True):
                                st.markdown(f"## {item['emoji']}")
                                st.markdown(f"**{item['tag']}**")
                                st.caption(item["category"])

                # =================================================
                # 18. DOWNLOAD JSON - NO JSON DISPLAY
                # =================================================

                st.divider()

                json_output = json.dumps(
                    {
                        "caption": result["caption"],
                        "image_category": result["image_category"],
                        "tags": tags
                    },
                    ensure_ascii=False,
                    indent=4
                )

                st.download_button(
                    label="⬇️ Download Tags as JSON",
                    data=json_output,
                    file_name=f"{filename.rsplit('.', 1)[0]}_tags.json",
                    mime="application/json",
                    use_container_width=True,
                    key=f"download_{image_id}"
                )

        except Exception as exc:
            st.error(
                f"Image processing error for {filename}: {exc}"
            )

else:
    st.info(
        "👆 Upload an image to preview it and generate "
        "structured AI tags."
    )


# =====================================================
# 19. FOOTER
# =====================================================

st.divider()

footer1, footer2 = st.columns(2)

with footer1:
    st.caption("✨ IMAGEAI | Smart Image Tag Generator")

with footer2:
    st.caption(
        "Powered by Python • Streamlit • Google Gemini AI"
    )