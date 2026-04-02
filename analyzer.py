import cv2
import numpy as np

def analyze_logo(image_path):
    image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)

    if image is None:
        return {
            "overall_score": 0,
            "contrast_score": 0,
            "complexity_score": 0,
            "balance_score": 0,
            "logo_likelihood_score": 0,
            "logo_class": "Uncertain / Non-logo-like",
            "logo_like": False,
            "feedback": "The image could not be analysed. Please upload a valid PNG or JPG logo file."
        }

    # Handle transparency
    if len(image.shape) == 3 and image.shape[2] == 4:
        alpha = image[:, :, 3]
        bgr = image[:, :, :3]
        white_bg = np.ones_like(bgr, dtype=np.uint8) * 255
        alpha_f = alpha[:, :, np.newaxis] / 255.0
        image = (bgr * alpha_f + white_bg * (1 - alpha_f)).astype(np.uint8)
    elif len(image.shape) == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape


    # Core visual metrics
    contrast = np.std(gray)
    contrast_score = min(max(int(contrast * 1.35), 0), 100)

    edges = cv2.Canny(gray, 100, 200)
    edge_density = np.sum(edges > 0) / edges.size
    complexity_score = max(0, 100 - int(edge_density * 360))

    left_half = gray[:, :w // 2]
    right_half = gray[:, w // 2:]
    top_half = gray[:h // 2, :]
    bottom_half = gray[h // 2:, :]

    lr_diff = abs(np.mean(left_half) - np.mean(right_half))
    tb_diff = abs(np.mean(top_half) - np.mean(bottom_half))
    balance_difference = (lr_diff + tb_diff) / 2
    balance_score = max(0, 100 - int(balance_difference * 1.1))

    contrast_score = min(max(contrast_score, 0), 100)
    complexity_score = min(max(complexity_score, 0), 100)
    balance_score = min(max(balance_score, 0), 100)


    # Stronger logo-like detection
    small = cv2.resize(image, (120, 120))
    pixels = small.reshape((-1, 3))

    quantized = (pixels // 32) * 32
    unique_colors = len(np.unique(quantized, axis=0))

    # Photo-likeness indicators
    hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
    sat_std = np.std(hsv[:, :, 1])
    val_std = np.std(hsv[:, :, 2])

    hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).flatten()
    hist = hist / np.sum(hist)
    entropy = -np.sum([p * np.log2(p) for p in hist if p > 0])

    center = gray[h // 4: 3 * h // 4, w // 4: 3 * w // 4]
    center_std = np.std(center)
    full_std = np.std(gray)

    # Logo positive scoring
    logo_score = 0

    if unique_colors <= 20:
        logo_score += 35
    elif unique_colors <= 50:
        logo_score += 28
    elif unique_colors <= 100:
        logo_score += 20
    elif unique_colors <= 180:
        logo_score += 10
    else:
        logo_score += 0

    if edge_density < 0.02:
        logo_score += 25
    elif edge_density < 0.05:
        logo_score += 20
    elif edge_density < 0.08:
        logo_score += 12
    else:
        logo_score += 0

    if center_std >= full_std * 0.85:
        logo_score += 20
    else:
        logo_score += 8

    if entropy < 5.2:
        logo_score += 20
    elif entropy < 6.0:
        logo_score += 12
    else:
        logo_score += 0

    # Photo penalty
    photo_penalty = 0

    if unique_colors > 220:
        photo_penalty += 20
    elif unique_colors > 140:
        photo_penalty += 10

    if entropy > 6.5:
        photo_penalty += 20
    elif entropy > 5.8:
        photo_penalty += 10

    if sat_std > 55 and val_std > 55:
        photo_penalty += 15

    if edge_density > 0.10:
        photo_penalty += 15
    elif edge_density > 0.07:
        photo_penalty += 8

    logo_likelihood_score = max(0, min(100, logo_score - photo_penalty + 20))

    if logo_likelihood_score >= 75:
        logo_class = "Likely Logo"
        logo_like = True
    elif logo_likelihood_score >= 55:
        logo_class = "Possibly Logo"
        logo_like = True
    else:
        logo_class = "Uncertain / Non-logo-like"
        logo_like = False

    raw_overall_score = int((contrast_score + complexity_score + balance_score) / 3)

    if logo_class == "Likely Logo":
        overall_score = raw_overall_score
    elif logo_class == "Possibly Logo":
        overall_score = int(raw_overall_score * 0.72)
    else:
        overall_score = int(raw_overall_score * 0.35)

    overall_score = min(max(overall_score, 0), 100)

    logo_suitability_score = int((overall_score * 0.6) + (logo_likelihood_score * 0.4))

    if not logo_like:
        logo_suitability_score = int(logo_suitability_score * 0.6)

    logo_suitability_score = min(max(logo_suitability_score, 0), 100)

    overall_score = min(max(overall_score, 0), 100)


    # feedback
    intro = ""
    contrast_text = ""
    complexity_text = ""
    balance_text = ""
    special_text = ""
    conclusion = ""

    if logo_class == "Likely Logo":
        if unique_colors <= 20:
            intro = "The uploaded image strongly resembles a logo, especially because of its limited colour palette and controlled visual structure."
        elif edge_density < 0.03:
            intro = "The uploaded image appears highly logo-like due to its clean edge profile and focused composition."
        else:
            intro = "The uploaded image is consistent with a conventional logo and shows clear logo-like properties."
    elif logo_class == "Possibly Logo":
        if unique_colors > 120:
            intro = "The uploaded image shows some logo-like features, but the broader colour range makes the classification less certain."
        elif entropy > 5.8:
            intro = "The uploaded image may represent a logo, although its visual information density introduces some uncertainty."
        else:
            intro = "The uploaded image has several logo-like characteristics, but the system cannot classify it with full confidence."
    else:
        if unique_colors > 180 and entropy > 6.0:
            intro = "The uploaded image behaves more like a photograph or detailed illustration than a conventional logo."
        elif edge_density > 0.08:
            intro = "The uploaded image contains substantial visual detail, which reduces its similarity to a typical logo."
        else:
            intro = "The uploaded image does not strongly match the structural qualities usually associated with logos."

    if contrast_score >= 85:
        contrast_text = "Contrast is very strong, which supports visibility across different backgrounds and sizes."
    elif contrast_score >= 65:
        contrast_text = "Contrast is good and should provide acceptable readability in most common uses."
    elif contrast_score >= 45:
        contrast_text = "Contrast is moderate, so stronger separation between elements could improve recognition."
    else:
        contrast_text = "Contrast is weak and may reduce clarity, especially in smaller or lower-quality reproductions."

    if complexity_score >= 85:
        complexity_text = "The visual structure is clean and economical, which is usually beneficial for scalability."
    elif complexity_score >= 65:
        complexity_text = "The design remains reasonably clear, although some detail may become less effective when reduced in size."
    elif complexity_score >= 45:
        complexity_text = "The image shows a noticeable level of complexity, which may weaken clarity in some use cases."
    else:
        complexity_text = "The image is visually busy and may not scale effectively as a mark or symbol."

    if balance_score >= 85:
        balance_text = "The composition appears balanced and visually stable."
    elif balance_score >= 65:
        balance_text = "The composition is generally balanced, though some areas may still carry slightly uneven visual weight."
    elif balance_score >= 45:
        balance_text = "The composition shows some imbalance, which may affect harmony."
    else:
        balance_text = "The composition feels uneven and may reduce the professional impression of the design."

    if not logo_like:
        if unique_colors > 180:
            special_text = "A very broad colour range suggests that the uploaded image may contain scene-like or photographic content."
        elif entropy > 6.0:
            special_text = "The image contains a high amount of visual information, which is less typical of clean logo marks."
        elif edge_density > 0.08:
            special_text = "Dense edge structure indicates detail that is more common in photographs than in simplified identity marks."
        else:
            special_text = "The system therefore treats the result as a limited visual assessment rather than a definitive logo evaluation."
    else:
        if overall_score >= 90:
            special_text = "This makes the design especially suitable for strong recognition and consistent application."
        elif overall_score >= 75:
            special_text = "This suggests that the design has solid practical potential in branding contexts."
        else:
            special_text = "Some refinement could still improve consistency and impact."

    if logo_like:
        if overall_score >= 85:
            conclusion = "Overall, the uploaded design performs strongly across the measured visual criteria."
        elif overall_score >= 65:
            conclusion = "Overall, the uploaded design performs reasonably well, although some refinement could strengthen it."
        else:
            conclusion = "Overall, the uploaded design shows potential but would benefit from further refinement."
    else:
        if overall_score >= 45:
            conclusion = "Overall, the visual metrics show some strengths, but the image should not be interpreted as a strong logo candidate."
        else:
            conclusion = "Overall, the uploaded image is not well suited to be interpreted as a conventional logo."

    feedback = " ".join([intro, conclusion, contrast_text, complexity_text, balance_text, special_text])

    return {
        "overall_score": overall_score,
        "contrast_score": contrast_score,
        "complexity_score": complexity_score,
        "balance_score": balance_score,
        "logo_likelihood_score": logo_likelihood_score,
        "logo_suitability_score": logo_suitability_score,
        "logo_class": logo_class,
        "logo_like": logo_like,
        "feedback": feedback
    }