"""
قائمة أسهم السوق السعودي الرئيسي (تاسي)
Saudi Main Market Stocks (TASI)
"""

# جميع أسهم السوق السعودي الرئيسي (تاسي) - محدث 2024
TASI_STOCKS = {
    # قطاع الطاقة
    "2222": {"name": "أرامكو السعودية", "sector": "الطاقة", "english": "Saudi Aramco"},
    "2030": {"name": "المصافي", "sector": "الطاقة", "english": "SARCO"},
    "2380": {"name": "بترورابغ", "sector": "الطاقة", "english": "Petro Rabigh"},
    "4030": {"name": "البحري", "sector": "النقل", "english": "Bahri"},
    "4200": {"name": "الدريس", "sector": "الطاقة", "english": "Aldrees"},
    "4050": {"name": "ساسكو", "sector": "الطاقة", "english": "SASCO"},

    # قطاع البنوك
    "1180": {"name": "الأهلي السعودي", "sector": "البنوك", "english": "SNB"},
    "1120": {"name": "الراجحي", "sector": "البنوك", "english": "Al Rajhi Bank"},
    "1010": {"name": "الرياض", "sector": "البنوك", "english": "Riyad Bank"},
    "1020": {"name": "الجزيرة", "sector": "البنوك", "english": "Bank AlJazira"},
    "1030": {"name": "الاستثمار", "sector": "البنوك", "english": "SAIB"},
    "1050": {"name": "بي اس اف", "sector": "البنوك", "english": "BSF"},
    "1060": {"name": "الأول", "sector": "البنوك", "english": "SAB"},
    "1080": {"name": "العربي", "sector": "البنوك", "english": "ANB"},
    "1140": {"name": "البلاد", "sector": "البنوك", "english": "Bank Albilad"},
    "1150": {"name": "الإنماء", "sector": "البنوك", "english": "Alinma Bank"},

    # قطاع المواد الأساسية
    "2010": {"name": "سابك", "sector": "المواد الأساسية", "english": "SABIC"},
    "2350": {"name": "كيان السعودية", "sector": "المواد الأساسية", "english": "KAYAN"},
    "1211": {"name": "معادن", "sector": "المواد الأساسية", "english": "Maaden"},
    "2001": {"name": "كيمانول", "sector": "المواد الأساسية", "english": "Chemanol"},
    "2060": {"name": "التصنيع", "sector": "المواد الأساسية", "english": "TASNEE"},
    "2110": {"name": "أنابيب السعودية", "sector": "المواد الأساسية", "english": "SPC"},
    "2170": {"name": "اللجين", "sector": "المواد الأساسية", "english": "Alujain"},
    "2290": {"name": "ينساب", "sector": "المواد الأساسية", "english": "Yansab"},
    "2310": {"name": "سبكيم العالمية", "sector": "المواد الأساسية", "english": "SIPCHEM"},
    "2250": {"name": "المجموعة السعودية", "sector": "المواد الأساسية", "english": "SIGC"},
    "2210": {"name": "نماء للكيماويات", "sector": "المواد الأساسية", "english": "Nama Chemicals"},
    "2240": {"name": "الزامل للصناعة", "sector": "المواد الأساسية", "english": "Zamil Industrial"},
    "2330": {"name": "المتقدمة", "sector": "المواد الأساسية", "english": "Advanced"},
    "2002": {"name": "بتروكيم", "sector": "المواد الأساسية", "english": "Petrochem"},
    "2180": {"name": "فيبكو", "sector": "المواد الأساسية", "english": "FIPCO"},
    "2220": {"name": "معدنية", "sector": "المواد الأساسية", "english": "MESC"},
    "2320": {"name": "البابطين", "sector": "المواد الأساسية", "english": "Babtain"},
    "1320": {"name": "أنابيب الشرق", "sector": "المواد الأساسية", "english": "MEPCO"},
    "1301": {"name": "أسلاك", "sector": "المواد الأساسية", "english": "Aslak"},
    "1304": {"name": "الكابلات", "sector": "المواد الأساسية", "english": "Cables"},
    "2300": {"name": "صناعة الورق", "sector": "المواد الأساسية", "english": "SPIMACO"},

    # قطاع الأسمنت
    "3010": {"name": "أسمنت العربية", "sector": "الأسمنت", "english": "Arabian Cement"},
    "3020": {"name": "أسمنت اليمامة", "sector": "الأسمنت", "english": "Yamama Cement"},
    "3030": {"name": "أسمنت السعودية", "sector": "الأسمنت", "english": "Saudi Cement"},
    "3040": {"name": "أسمنت القصيم", "sector": "الأسمنت", "english": "Qassim Cement"},
    "3050": {"name": "أسمنت الجنوب", "sector": "الأسمنت", "english": "Southern Cement"},
    "3060": {"name": "أسمنت ينبع", "sector": "الأسمنت", "english": "Yanbu Cement"},
    "3080": {"name": "أسمنت الشرقية", "sector": "الأسمنت", "english": "Eastern Cement"},
    "3090": {"name": "أسمنت تبوك", "sector": "الأسمنت", "english": "Tabuk Cement"},
    "3091": {"name": "أسمنت الجوف", "sector": "الأسمنت", "english": "Jouf Cement"},
    "3001": {"name": "حديد وطني", "sector": "الأسمنت", "english": "National Steel"},
    "3002": {"name": "أسمنت نجران", "sector": "الأسمنت", "english": "Najran Cement"},
    "3003": {"name": "أسمنت المدينة", "sector": "الأسمنت", "english": "City Cement"},
    "3004": {"name": "أسمنت الشمالية", "sector": "الأسمنت", "english": "Northern Cement"},
    "3005": {"name": "أسمنت أم القرى", "sector": "الأسمنت", "english": "Umm Al-Qura Cement"},
    "3007": {"name": "الواحة", "sector": "الأسمنت", "english": "Al Waha"},

    # قطاع التجزئة
    "4003": {"name": "إكسترا", "sector": "التجزئة", "english": "eXtra"},
    "4190": {"name": "جرير", "sector": "التجزئة", "english": "Jarir"},
    "2090": {"name": "جرير", "sector": "التجزئة", "english": "Jarir"},
    "4008": {"name": "ساكو", "sector": "التجزئة", "english": "SACO"},
    "4009": {"name": "المجموعة المتحدة", "sector": "التجزئة", "english": "United Group"},
    "4081": {"name": "النهدي الطبية", "sector": "التجزئة", "english": "Al Nahdi"},
    "4006": {"name": "الدوائية", "sector": "التجزئة", "english": "SPIMACO"},
    "4180": {"name": "مبكو", "sector": "التجزئة", "english": "MEPCO"},
    "4160": {"name": "ثمار", "sector": "التجزئة", "english": "Themar"},
    "4161": {"name": "أكوا باور", "sector": "التجزئة", "english": "ACWA Power"},
    "4290": {"name": "الخليج للتدريب", "sector": "التجزئة", "english": "Gulf Training"},

    # قطاع إنتاج الأغذية
    "2020": {"name": "المراعي", "sector": "إنتاج الأغذية", "english": "Almarai"},
    "2050": {"name": "صافولا", "sector": "إنتاج الأغذية", "english": "Savola"},
    "6010": {"name": "نادك", "sector": "إنتاج الأغذية", "english": "NADEC"},
    "6001": {"name": "حلواني إخوان", "sector": "إنتاج الأغذية", "english": "Halwani Bros"},
    "6002": {"name": "هرفي للأغذية", "sector": "إنتاج الأغذية", "english": "Herfy Foods"},
    "6004": {"name": "الكفو الصناعية", "sector": "إنتاج الأغذية", "english": "Al Kafu"},
    "6012": {"name": "أمريكانا", "sector": "إنتاج الأغذية", "english": "Americana"},
    "6013": {"name": "التنمية الغذائية", "sector": "إنتاج الأغذية", "english": "SFDA"},
    "6014": {"name": "الجوف الزراعية", "sector": "إنتاج الأغذية", "english": "Al-Jouf"},
    "6015": {"name": "الشرقية الزراعية", "sector": "إنتاج الأغذية", "english": "SIDC"},
    "6020": {"name": "جاكو", "sector": "إنتاج الأغذية", "english": "Jaco"},
    "6040": {"name": "تبوك الزراعية", "sector": "إنتاج الأغذية", "english": "TADCO"},
    "6050": {"name": "حائل الزراعية", "sector": "إنتاج الأغذية", "english": "HAACO"},
    "6060": {"name": "الشرقية للتنمية", "sector": "إنتاج الأغذية", "english": "Astra Agro"},
    "6070": {"name": "الأسماك", "sector": "إنتاج الأغذية", "english": "NFPC"},
    "6090": {"name": "جازادكو", "sector": "إنتاج الأغذية", "english": "JADCO"},

    # قطاع تجزئة الأغذية
    "4210": {"name": "أسواق العثيم", "sector": "تجزئة الأغذية", "english": "Othaim Markets"},
    "4001": {"name": "أسترا الصناعية", "sector": "السلع الرأسمالية", "english": "Astra Industrial"},
    "4240": {"name": "الحكير", "sector": "تجزئة الأغذية", "english": "Alhokair"},
    "4280": {"name": "المتحدة الدولية", "sector": "تجزئة الأغذية", "english": "UIHC"},
    "4260": {"name": "بدجت السعودية", "sector": "تجزئة الأغذية", "english": "Budget Saudi"},
    "4261": {"name": "لولو هايبر", "sector": "تجزئة الأغذية", "english": "Lulu"},

    # قطاع الرعاية الصحية
    "4002": {"name": "المواساة", "sector": "الرعاية الصحية", "english": "Mouwasat"},
    "4004": {"name": "دله الصحية", "sector": "الرعاية الصحية", "english": "Dallah Health"},
    "4005": {"name": "رعاية", "sector": "الرعاية الصحية", "english": "CARE"},
    "4007": {"name": "الحمادي", "sector": "الرعاية الصحية", "english": "Al-Hammadi"},
    "4010": {"name": "الأدوية", "sector": "الرعاية الصحية", "english": "SAJA Pharma"},
    "4011": {"name": "سيرا", "sector": "الرعاية الصحية", "english": "Seera"},
    "4012": {"name": "أبو معطي", "sector": "الرعاية الصحية", "english": "Abo Moati"},
    "4013": {"name": "سوليدرتي السعودية", "sector": "الرعاية الصحية", "english": "Solidarity"},
    "4014": {"name": "دار المعدات", "sector": "الرعاية الصحية", "english": "Dar Al Maadat"},
    "4015": {"name": "سولدرتي تكافل", "sector": "الرعاية الصحية", "english": "Solidarity Takaful"},
    "4016": {"name": "المصافي", "sector": "الرعاية الصحية", "english": "SARCO"},
    "4017": {"name": "فقيه الطبية", "sector": "الرعاية الصحية", "english": "Fakeeh"},
    "4018": {"name": "الحبيب الطبية", "sector": "الرعاية الصحية", "english": "Al Habib"},

    # قطاع العقارات
    "4250": {"name": "جبل عمر", "sector": "إدارة وتطوير العقارات", "english": "Jabal Omar"},
    "4300": {"name": "دار الأركان", "sector": "إدارة وتطوير العقارات", "english": "Dar Al Arkan"},
    "4310": {"name": "مكة للإنشاء", "sector": "إدارة وتطوير العقارات", "english": "MCC"},
    "4320": {"name": "أرنب", "sector": "إدارة وتطوير العقارات", "english": "Retal"},
    "4321": {"name": "رتال للتطوير", "sector": "إدارة وتطوير العقارات", "english": "Retal Development"},
    "4322": {"name": "أريد", "sector": "إدارة وتطوير العقارات", "english": "Areed"},
    "4323": {"name": "سمو العقارية", "sector": "إدارة وتطوير العقارات", "english": "Sumo"},
    "4330": {"name": "الرياض للتعمير", "sector": "إدارة وتطوير العقارات", "english": "Riyadh Development"},
    "4331": {"name": "مدينة المعرفة", "sector": "إدارة وتطوير العقارات", "english": "KAEC"},
    "4332": {"name": "الأندلس العقارية", "sector": "إدارة وتطوير العقارات", "english": "Andalus"},
    "4333": {"name": "جدوى ريت", "sector": "إدارة وتطوير العقارات", "english": "Jadwa REIT"},
    "4334": {"name": "الأهلي ريت", "sector": "إدارة وتطوير العقارات", "english": "SNB REIT"},
    "4335": {"name": "الراجحي ريت", "sector": "إدارة وتطوير العقارات", "english": "Riyad REIT"},
    "4336": {"name": "ملكية للاستثمار", "sector": "إدارة وتطوير العقارات", "english": "MISA"},
    "4337": {"name": "الراجحي ريت", "sector": "إدارة وتطوير العقارات", "english": "Rajhi REIT"},
    "4338": {"name": "سويكورب وابل ريت", "sector": "إدارة وتطوير العقارات", "english": "Swicorp REIT"},
    "4339": {"name": "بوان", "sector": "إدارة وتطوير العقارات", "english": "Bawan"},
    "4340": {"name": "الأمانة ريت", "sector": "إدارة وتطوير العقارات", "english": "Amanah REIT"},
    "4342": {"name": "إتقان ريت", "sector": "إدارة وتطوير العقارات", "english": "Itqan REIT"},
    "4344": {"name": "سدكو ريت", "sector": "إدارة وتطوير العقارات", "english": "SEDCO REIT"},
    "4345": {"name": "تعليم ريت", "sector": "إدارة وتطوير العقارات", "english": "Taleem REIT"},
    "4346": {"name": "مشاركة ريت", "sector": "إدارة وتطوير العقارات", "english": "Musharaka REIT"},
    "4347": {"name": "ينسون", "sector": "إدارة وتطوير العقارات", "english": "YNSON"},
    "4348": {"name": "جازان ريت", "sector": "إدارة وتطوير العقارات", "english": "Jazan REIT"},

    # قطاع الاتصالات
    "7010": {"name": "اس تي سي", "sector": "الاتصالات", "english": "STC"},
    "7020": {"name": "الاتصالات", "sector": "الاتصالات", "english": "Mobily"},
    "7030": {"name": "زين السعودية", "sector": "الاتصالات", "english": "Zain KSA"},
    "7040": {"name": "عذيب", "sector": "الاتصالات", "english": "Etihad Atheeb"},

    # قطاع التأمين
    "8010": {"name": "التعاونية", "sector": "التأمين", "english": "Tawuniya"},
    "8020": {"name": "ملاذ للتأمين", "sector": "التأمين", "english": "Malath"},
    "8030": {"name": "ميدغلف للتأمين", "sector": "التأمين", "english": "MedGulf"},
    "8040": {"name": "أليانز إس إف", "sector": "التأمين", "english": "Allianz SF"},
    "8050": {"name": "سلامة", "sector": "التأمين", "english": "Salama"},
    "8060": {"name": "ولاء للتأمين", "sector": "التأمين", "english": "Walaa"},
    "8070": {"name": "الأهلية للتأمين", "sector": "التأمين", "english": "Al-Ahlia"},
    "8080": {"name": "ساب تكافل", "sector": "التأمين", "english": "SABB Takaful"},
    "8100": {"name": "سايكو", "sector": "التأمين", "english": "Saico"},
    "8120": {"name": "الاتحاد للتأمين", "sector": "التأمين", "english": "Union"},
    "8150": {"name": "أسيج", "sector": "التأمين", "english": "ACIG"},
    "8160": {"name": "التأمين العربية", "sector": "التأمين", "english": "Arabian Insurance"},
    "8170": {"name": "الأهلي للتكافل", "sector": "التأمين", "english": "Al Ahli Takaful"},
    "8180": {"name": "الصقر للتأمين", "sector": "التأمين", "english": "Al-Sagr"},
    "8190": {"name": "المتحدة للتأمين", "sector": "التأمين", "english": "United"},
    "8200": {"name": "الإعادة السعودية", "sector": "التأمين", "english": "Saudi Re"},
    "8210": {"name": "بوبا العربية", "sector": "التأمين", "english": "Bupa Arabia"},
    "8230": {"name": "الراجحي للتأمين", "sector": "التأمين", "english": "Al Rajhi Takaful"},
    "8240": {"name": "أكسا التعاونية", "sector": "التأمين", "english": "AXA Cooperative"},
    "8250": {"name": "الخليج العامة", "sector": "التأمين", "english": "Gulf General"},
    "8260": {"name": "الخليجية العامة", "sector": "التأمين", "english": "Gulf General"},
    "8270": {"name": "بروج للتأمين", "sector": "التأمين", "english": "Buruj"},
    "8280": {"name": "العالمية للتأمين", "sector": "التأمين", "english": "Allianz Global"},
    "8300": {"name": "الوطنية للتأمين", "sector": "التأمين", "english": "Wataniya"},
    "8310": {"name": "أمانة للتأمين", "sector": "التأمين", "english": "Amanah"},
    "8311": {"name": "عناية", "sector": "التأمين", "english": "Enaya"},
    "8312": {"name": "آسيا للتأمين", "sector": "التأمين", "english": "Asia Care"},

    # قطاع المرافق العامة
    "2070": {"name": "الغاز", "sector": "المرافق العامة", "english": "Saudi Gas"},
    "2080": {"name": "الغاز والتصنيع", "sector": "المرافق العامة", "english": "GASCO"},
    "2081": {"name": "أكوا باور", "sector": "المرافق العامة", "english": "ACWA Power"},
    "2082": {"name": "أرامكو للتوزيع", "sector": "المرافق العامة", "english": "Aramco Dist"},
    "2083": {"name": "مرافق", "sector": "المرافق العامة", "english": "Marafiq"},
    "5110": {"name": "السعودية للكهرباء", "sector": "المرافق العامة", "english": "SEC"},

    # قطاع النقل
    "4031": {"name": "الخطوط السعودية", "sector": "النقل", "english": "Saudia"},
    "4040": {"name": "سابتكو", "sector": "النقل", "english": "SAPTCO"},
    "4070": {"name": "بدجت السعودية", "sector": "النقل", "english": "Budget Saudi"},
    "4080": {"name": "سنومي", "sector": "النقل", "english": "Senomai"},
    "4100": {"name": "مكة للإنشاء", "sector": "النقل", "english": "MCDC"},
    "4110": {"name": "باتك", "sector": "النقل", "english": "BATEC"},
    "4130": {"name": "الباحة", "sector": "النقل", "english": "Al Baha"},
    "4140": {"name": "صادرات", "sector": "النقل", "english": "SADERAT"},
    "4150": {"name": "التصنيع الوطنية", "sector": "النقل", "english": "NIC"},
    "4170": {"name": "شمس", "sector": "النقل", "english": "SHAMS"},

    # قطاع السلع الرأسمالية
    "1201": {"name": "تكوين", "sector": "السلع الرأسمالية", "english": "Takween"},
    "1202": {"name": "مبكو", "sector": "السلع الرأسمالية", "english": "MEPCO"},
    "1210": {"name": "بي سي آي", "sector": "السلع الرأسمالية", "english": "BCI"},
    "1212": {"name": "أسترا الصناعية", "sector": "السلع الرأسمالية", "english": "Astra"},
    "1213": {"name": "نسيج", "sector": "السلع الرأسمالية", "english": "Naseej"},
    "1214": {"name": "شاكر", "sector": "السلع الرأسمالية", "english": "Shaker"},
    "1820": {"name": "مجموعة الحكير", "sector": "السلع الرأسمالية", "english": "Alhokair Group"},
    "2040": {"name": "الخزف", "sector": "السلع الرأسمالية", "english": "SCP"},
    "2130": {"name": "صدق", "sector": "السلع الرأسمالية", "english": "SIDQ"},
    "2140": {"name": "أيان للاستثمار", "sector": "السلع الرأسمالية", "english": "Ayan"},
    "2150": {"name": "زهرة الواحة", "sector": "السلع الرأسمالية", "english": "Zahrat"},
    "2160": {"name": "أماك", "sector": "السلع الرأسمالية", "english": "AMAK"},
    "2190": {"name": "سيسكو القابضة", "sector": "السلع الرأسمالية", "english": "SISCO"},
    "2200": {"name": "أنابيب", "sector": "السلع الرأسمالية", "english": "Arabian Pipes"},
    "2230": {"name": "الكيميائية", "sector": "السلع الرأسمالية", "english": "Chemical"},
    "2270": {"name": "سدافكو", "sector": "السلع الرأسمالية", "english": "SADAFCO"},
    "2280": {"name": "المتحدة للصناعة", "sector": "السلع الرأسمالية", "english": "SIDC"},
    "2340": {"name": "العبد اللطيف", "sector": "السلع الرأسمالية", "english": "Abdullatif"},
    "2360": {"name": "الفخارية", "sector": "السلع الرأسمالية", "english": "Saudi Ceramic"},
    "2370": {"name": "مسك", "sector": "السلع الرأسمالية", "english": "MISK"},

    # قطاع الخدمات التجارية
    "1831": {"name": "لجام للرياضة", "sector": "الخدمات التجارية", "english": "Leejam Sports"},
    "1832": {"name": "صدارة", "sector": "الخدمات التجارية", "english": "Sadara"},
    "1833": {"name": "الصناعات الكهربائية", "sector": "الخدمات التجارية", "english": "EIC"},
    "4012": {"name": "الصحراء", "sector": "الخدمات التجارية", "english": "Sahara"},
    "4020": {"name": "العقارية", "sector": "الخدمات التجارية", "english": "SRECO"},
    "4220": {"name": "إمكان التعليمية", "sector": "الخدمات التجارية", "english": "Emkan"},
    "4230": {"name": "الباحة للاستثمار", "sector": "الخدمات التجارية", "english": "Baha Invest"},
    "4270": {"name": "طيبة", "sector": "الخدمات التجارية", "english": "Taiba"},

    # قطاع الإعلام والترفيه
    "4070": {"name": "تهامة للإعلان", "sector": "الإعلام والترفيه", "english": "Tihama"},
    "4071": {"name": "العربية للإعلام", "sector": "الإعلام والترفيه", "english": "Arabia Media"},
    "4090": {"name": "سيرا القابضة", "sector": "الإعلام والترفيه", "english": "Seera Holding"},
    "4291": {"name": "الوطنية للتعليم", "sector": "الإعلام والترفيه", "english": "NELC"},
    "4292": {"name": "المعرفة المالية", "sector": "الإعلام والترفيه", "english": "KAEC"},
}

# قائمة القطاعات
SECTORS = [
    "الطاقة",
    "البنوك",
    "المواد الأساسية",
    "الأسمنت",
    "التجزئة",
    "إنتاج الأغذية",
    "تجزئة الأغذية",
    "الرعاية الصحية",
    "إدارة وتطوير العقارات",
    "الاتصالات",
    "التأمين",
    "المرافق العامة",
    "النقل",
    "السلع الرأسمالية",
    "الخدمات التجارية",
    "الإعلام والترفيه"
]

def get_stock_info(code: str) -> dict:
    """الحصول على معلومات السهم"""
    code = code.strip().replace(".SR", "")
    if code in TASI_STOCKS:
        return TASI_STOCKS[code]
    return None

def get_all_stocks() -> list:
    """الحصول على جميع الأسهم"""
    return [
        {"code": code, "symbol": code, **info}
        for code, info in TASI_STOCKS.items()
    ]

def search_stocks(query: str) -> list:
    """البحث عن الأسهم"""
    query = query.strip().upper()
    results = []
    for code, info in TASI_STOCKS.items():
        if (query in code or
            query in info["name"].upper() or
            query in info.get("english", "").upper()):
            results.append({"code": code, "symbol": code, **info})
    return results[:30]

def get_stocks_by_sector(sector: str) -> list:
    """الحصول على أسهم قطاع معين"""
    return [
        {"code": code, "symbol": code, **info}
        for code, info in TASI_STOCKS.items()
        if info["sector"] == sector
    ]
