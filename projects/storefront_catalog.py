"""Fictional fixtures only: never an inventory or payment authority."""


def storefront_catalog(lang):
    fa = lang == "fa"
    def text(a, b):
        return a if fa else b
    rows = [
        ("avid", "گلدان آوید · مجسمه‌ای", "Avid sculptural vase", "decor", "ceramic", 1280000, "سرامیک دست‌پرداخت", "Hand-finished ceramic", "۲۸ × ۱۴ سانتی‌متر", "28 × 14 cm", "فرمی آرام برای شاخه‌های خشک و گوشه روشن خانه.", "A quiet silhouette for dried stems and sunlit corners."),
        ("soha", "سها · چراغ رومیزی", "Soha table light", "lighting", "lamp", 2490000, "فلز برس‌خورده، LED", "Brushed metal, LED", "ارتفاع ۳۶ سانتی‌متر", "36 cm tall", "نور گرم و پخش‌شده برای میز مطالعه و کنار تخت.", "Warm, diffused light for a reading desk or bedside."),
        ("palm", "پالم · رانر نخی", "Palm cotton runner", "textile", "textile", 980000, "پنبه طبیعی", "Natural cotton", "۱۴۰ × ۴۰ سانتی‌متر", "140 × 40 cm", "بافت ملایم و حاشیه ساده برای میزهای روزمره.", "A soft weave and understated edge for everyday tables."),
        ("luna", "لونا · کاسه پذیرایی", "Luna serving bowl", "decor", "bowl", 760000, "سرامیک لعاب‌دار", "Glazed ceramic", "قطر ۲۴ سانتی‌متر", "24 cm diameter", "یک ظرف کم‌عمق برای میوه، پذیرایی یا اشیای کوچک.", "A low-profile bowl for fruit, shared bites or small treasures."),
        ("nook", "نوک · کوسن بافت‌دار", "Nook textured cushion", "textile", "cushion", 890000, "روکش پنبه، زیپ مخفی", "Cotton cover, concealed zip", "۴۵ × ۴۵ سانتی‌متر", "45 × 45 cm", "بافت برجسته‌ای که بدون شلوغی به نشیمن عمق می‌دهد.", "Tactile texture that adds depth without visual noise."),
        ("halo", "هالو · چراغ دیواری", "Halo wall light", "lighting", "pendant", 1890000, "فلز رنگ‌شده، LED", "Coated metal, LED", "قطر ۲۰ سانتی‌متر", "20 cm diameter", "حلقه نور نرم برای راهرو و دیوار کنار تخت.", "A soft halo of light for hallways and bedside walls."),
    ]
    colors = [("sand", text("شنی", "Sand"), "#c7ab88"), ("olive", text("زیتونی", "Olive"), "#737a57"), ("ink", text("جوهر", "Ink"), "#303c40")]
    products = []
    large_sizes = [("ارتفاع ۳۶ سانتی‌متر", "36 cm tall"), ("ارتفاع ۴۴ سانتی‌متر", "44 cm tall"), ("۱۸۰ × ۴۰ سانتی‌متر", "180 × 40 cm"), ("قطر ۳۰ سانتی‌متر", "30 cm diameter"), ("۶۰ × ۶۰ سانتی‌متر", "60 × 60 cm"), ("قطر ۲۸ سانتی‌متر", "28 cm diameter")]
    for index, row in enumerate(rows):
        key, fa_name, en_name, category, art, price, fa_material, en_material, fa_size, en_size, fa_description, en_description = row
        sizes = [{"id": "standard", "label": text(fa_size, en_size)}, {"id": "large", "label": text(*large_sizes[index])}]
        care = {
            "textile": text("با آب سرد و شوینده ملایم بشویید؛ در سایه خشک کنید.", "Wash gently in cold water with mild detergent; dry in the shade."),
            "lighting": text("پیش از تمیزکردن از برق جدا کنید؛ فقط دستمال نرم و خشک استفاده کنید.", "Disconnect before cleaning; use only a soft, dry cloth."),
            "decor": text("با دستمال نرم و مرطوب تمیز کنید؛ از مواد ساینده استفاده نکنید.", "Clean with a soft, damp cloth; avoid abrasive cleaners."),
        }[category]
        products.append({"id": key, "name": text(fa_name, en_name), "category": category, "art": art, "price": price, "sizes": sizes, "colors": [{"id": key, "label": name} for key, name, _ in colors],
            "price_label": text(f"{price:,} تومان".translate(str.maketrans("0123456789,", "۰۱۲۳۴۵۶۷۸۹٬")), f"{price:,} Toman"),
            "description": text(fa_description, en_description),
            "variants": [{"id": color + "-" + size["id"], "color_id": color, "size_id": size["id"], "label": name + " · " + size["label"], "color": hex_color, "stock": 0 if index == 0 and color == "ink" else 6, "price": price + (100000 if color == "olive" else 0) + (250000 if size["id"] == "large" else 0)} for color, name, hex_color in colors for size in sizes],
            "specs": [{"label": text("جنس", "Material"), "value": text(fa_material, en_material)}, {"label": text("ابعاد", "Dimensions"), "value": text(fa_size, en_size)}],
            "care": care})
    return {"lang": "fa" if fa else "en", "products": products, "shipping": [
        {"id": "pickup", "label": text("تحویل حضوری · رایگان", "Studio pickup · free"), "fee": 0},
        {"id": "standard", "label": text("ارسال معمولی · ۳ تا ۵ روز · ۹۰٬۰۰۰ تومان", "Standard · 3–5 days · 90,000 Toman"), "fee": 90000},
        {"id": "express", "label": text("ارسال سریع · ۱ تا ۲ روز · ۱۵۰٬۰۰۰ تومان", "Express · 1–2 days · 150,000 Toman"), "fee": 150000}]}
