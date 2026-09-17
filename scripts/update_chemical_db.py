# scripts/update_chemical_db.py
import json

db_path = 'data/chemical_db/ins_codes.json'
with open(db_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

new_additives = [
    {
        'code': 'INS 635',
        'aliases': ['E635', '635', 'Disodium 5-ribonucleotides', 'Disodium Ribonucleotides', 'I+G', 'Flavor Enhancer 635', 'Flavour Enhancer 635'],
        'name': 'Disodium 5-ribonucleotides',
        'category': 'Flavor Enhancer',
        'risk_level': 'Moderate',
        'description': 'Synergistic umami enhancer combining inosinate and guanylate. 4x more potent than MSG alone; widely used in instant noodles, crisps, and tastemaker seasoning packets.',
        'health_warnings': ['Metabolizes into purines which rapidly elevate serum uric acid; can trigger acute gout flares. Suspected trigger for ribonucleotide contact dermatitis and asthmatic bronchospasms. Not permitted in infant foods.'],
        'contraindications': ['Gout', 'Hyperuricemia', 'Asthma', 'Infants & Young Children'],
        'is_disguised_sugar': False
    },
    {
        'code': 'INS 508',
        'aliases': ['E508', '508', 'Potassium Chloride', 'Thickener 508'],
        'name': 'Potassium Chloride',
        'category': 'Thickener / Gelling Agent / Mineral Salt',
        'risk_level': 'Safe',
        'description': 'Naturally occurring mineral salt used to firm noodle texture, maintain gluten elasticity, and serve as a sodium-reducing mineral agent.',
        'health_warnings': ['Generally recognized as safe; however, high potassium load is strictly contraindicated for patients with chronic kidney disease (CKD) who cannot excrete potassium.'],
        'contraindications': ['Chronic Kidney Disease (CKD)', 'Hyperkalemia'],
        'is_disguised_sugar': False
    },
    {
        'code': 'INS 412',
        'aliases': ['E412', '412', 'Guar Gum', 'Thickener 412'],
        'name': 'Guar Gum',
        'category': 'Thickener / Stabilizer',
        'risk_level': 'Safe',
        'description': 'Water-soluble natural fiber extracted from guar beans. Imparts viscous body and springiness to instant noodles and sauces.',
        'health_warnings': ['Generally safe prebiotic fiber. High dietary doses can cause abdominal gas, bloating, and gastrointestinal cramping in FODMAP-sensitive individuals.'],
        'contraindications': ['Severe IBS (FODMAP sensitive)'],
        'is_disguised_sugar': False
    },
    {
        'code': 'INS 501(i)',
        'aliases': ['E501(i)', '501(i)', 'E501', '501', 'Potassium Carbonate'],
        'name': 'Potassium Carbonate',
        'category': 'Acidity Regulator / Kansui Salt',
        'risk_level': 'Safe',
        'description': 'Traditional alkaline Kansui salt essential for giving instant ramen and noodles their characteristic chewy texture, springiness, and golden hue.',
        'health_warnings': ['Generally recognized as safe in customary food usage.'],
        'contraindications': [],
        'is_disguised_sugar': False
    },
    {
        'code': 'INS 451(ii)',
        'aliases': ['E451(ii)', '451(ii)', 'E451', '451', 'Sodium Tripolyphosphate', 'STPP', 'Humectant 451(ii)'],
        'name': 'Sodium Tripolyphosphate',
        'category': 'Humectant / Moisture Retainer',
        'risk_level': 'Moderate',
        'description': 'Inorganic polyphosphate salt used to retain moisture, prevent weeping, and accelerate rehydration of noodle strands in boiling water.',
        'health_warnings': ['Frequent consumption of industrial phosphate additives is clinically linked to elevated serum phosphate, vascular endothelial calcification, and increased cardiovascular and renal disease burden.'],
        'contraindications': ['Chronic Kidney Disease', 'Cardiovascular Disease', 'Hypertension'],
        'is_disguised_sugar': False
    },
    {
        'code': 'INS 451(i)',
        'aliases': ['E451(i)', '451(i)', 'Pentasodium Triphosphate'],
        'name': 'Pentasodium Triphosphate',
        'category': 'Humectant / Emulsifier',
        'risk_level': 'Moderate',
        'description': 'Phosphate salt used as a water-binding and emulsifying agent in processed meat and extruded starch products.',
        'health_warnings': ['Elevates dietary phosphate burden, placing strain on renal clearance pathways.'],
        'contraindications': ['Chronic Kidney Disease', 'Hypertension'],
        'is_disguised_sugar': False
    },
    {
        'code': 'INS 330',
        'aliases': ['E330', '330', 'Citric Acid', 'Acidity Regulator 330'],
        'name': 'Citric Acid',
        'category': 'Acidity Regulator / Antioxidant',
        'risk_level': 'Safe',
        'description': 'Naturally occurring fruit acid used industrially for tangy taste, antioxidant synergism, and microbial shelf-life preservation.',
        'health_warnings': ['Generally recognized as safe; high frequent exposure to acidic beverages and snacks can accelerate tooth enamel demineralization.'],
        'contraindications': ['Acid Reflux (GERD)'],
        'is_disguised_sugar': False
    },
    {
        'code': 'INS 627',
        'aliases': ['E627', '627', 'Disodium 5-guanylate', 'Disodium Guanylate', 'GMP'],
        'name': 'Disodium 5-guanylate',
        'category': 'Flavor Enhancer',
        'risk_level': 'Moderate',
        'description': 'Nucleotide flavor enhancer used alongside glutamate to create intense savory umami depth.',
        'health_warnings': ['Metabolizes to uric acid; contraindicated for individuals prone to gout.'],
        'contraindications': ['Gout', 'Hyperuricemia'],
        'is_disguised_sugar': False
    },
    {
        'code': 'INS 631',
        'aliases': ['E631', '631', 'Disodium 5-inosinate', 'Disodium Inosinate', 'IMP'],
        'name': 'Disodium 5-inosinate',
        'category': 'Flavor Enhancer',
        'risk_level': 'Moderate',
        'description': 'Nucleotide flavor enhancer frequently compounded with MSG to enhance palatability.',
        'health_warnings': ['Purine content contributes to elevated serum uric acid levels.'],
        'contraindications': ['Gout', 'Asthma'],
        'is_disguised_sugar': False
    },
    {
        'code': 'INS 319',
        'aliases': ['E319', '319', 'TBHQ', 'Tertiary Butylhydroquinone'],
        'name': 'Tertiary Butylhydroquinone',
        'category': 'Synthetic Antioxidant',
        'risk_level': 'High',
        'description': 'Petroleum-derived synthetic preservative sprayed into vegetable frying oils to prevent oxidation and rancidity in instant noodles and fried crisps.',
        'health_warnings': ['High-dose toxicology studies in animal models reveal cellular liver damage, vision alterations, and immunological impairment. Strictly restricted under food laws.'],
        'contraindications': ['Children', 'Immune Disorders', 'Liver Disease'],
        'is_disguised_sugar': False
    },
    {
        'code': 'INS 320',
        'aliases': ['E320', '320', 'BHA', 'Butylated Hydroxyanisole'],
        'name': 'Butylated Hydroxyanisole',
        'category': 'Synthetic Antioxidant',
        'risk_level': 'High',
        'description': 'Synthetic antioxidant preservative used to prevent fat spoilage in savory packaged goods.',
        'health_warnings': ['Classified by WHO/IARC as possibly carcinogenic to humans; documented endocrine disrupting activity.'],
        'contraindications': ['Children', 'Pregnancy'],
        'is_disguised_sugar': False
    },
    {
        'code': 'INS 321',
        'aliases': ['E321', '321', 'BHT', 'Butylated Hydroxytoluene'],
        'name': 'Butylated Hydroxytoluene',
        'category': 'Synthetic Antioxidant',
        'risk_level': 'High',
        'description': 'Synthetic fat-soluble antioxidant used in packaging liners and fried snack foods.',
        'health_warnings': ['Linked to hepatic and renal strain in animal bioassays.'],
        'contraindications': ['Children', 'Liver Disease'],
        'is_disguised_sugar': False
    },
    {
        'code': 'INS 110',
        'aliases': ['E110', '110', 'Sunset Yellow FCF', 'FD&C Yellow 6'],
        'name': 'Sunset Yellow FCF',
        'category': 'Synthetic Food Color',
        'risk_level': 'High',
        'description': 'Synthetic petroleum azo dye producing bright sunset-orange color in snacks, beverage powders, and candies.',
        'health_warnings': ['Southampton University research established strong links to attention deficit and hyperactivity in children. Frequent allergen for asthmatics.'],
        'contraindications': ['ADHD', 'Asthma', 'Aspirin Sensitivity', 'Children'],
        'is_disguised_sugar': False
    },
    {
        'code': 'INS 122',
        'aliases': ['E122', '122', 'Carmoisine', 'Azorubine'],
        'name': 'Carmoisine',
        'category': 'Synthetic Food Color',
        'risk_level': 'High',
        'description': 'Synthetic red coal-tar azo dye.',
        'health_warnings': ['Banned in the USA and Canada. Associated with hyperreactivity in young children and cutaneous urticaria.'],
        'contraindications': ['Children', 'Asthma', 'Skin Allergies'],
        'is_disguised_sugar': False
    },
    {
        'code': 'INS 171',
        'aliases': ['E171', '171', 'Titanium Dioxide'],
        'name': 'Titanium Dioxide',
        'category': 'Food Whitening Agent',
        'risk_level': 'High',
        'description': 'Inorganic white mineral pigment.',
        'health_warnings': ['BANNED in the European Union (EFSA 2021) as a food additive due to genotoxicity concerns and nanoparticle accumulation damaging cellular DNA.'],
        'contraindications': ['All Consumers (EFSA Genotoxicity Ban)'],
        'is_disguised_sugar': False
    },
    {
        'code': 'INS 415',
        'aliases': ['E415', '415', 'Xanthan Gum'],
        'name': 'Xanthan Gum',
        'category': 'Thickener / Stabilizer',
        'risk_level': 'Safe',
        'description': 'Bacterial fermentation polysaccharide providing stable viscosity across wide temperature and pH ranges.',
        'health_warnings': ['Generally recognized as safe; mild laxative effect if consumed in excess.'],
        'contraindications': [],
        'is_disguised_sugar': False
    },
    {
        'code': 'INS 466',
        'aliases': ['E466', '466', 'Sodium Carboxymethyl Cellulose', 'Cellulose Gum', 'CMC'],
        'name': 'Sodium Carboxymethyl Cellulose',
        'category': 'Thickener / Emulsifier',
        'risk_level': 'Moderate',
        'description': 'Modified cellulose ether used to thicken sauces, gravies, and bakery products.',
        'health_warnings': ['Peer-reviewed studies indicate CMC degrades intestinal mucus barriers, facilitating bacterial translocation and gut dysbiosis.'],
        'contraindications': ['Inflammatory Bowel Disease (IBD)', 'Colitis', 'Gut Inflammation'],
        'is_disguised_sugar': False
    },
    {
        'code': 'INS 472e',
        'aliases': ['E472e', '472e', 'DATEM'],
        'name': 'Diacetyl Tartaric Acid Esters of Mono- and Diglycerides',
        'category': 'Emulsifier / Dough Conditioner',
        'risk_level': 'Moderate',
        'description': 'Synthetic emulsifier used to build dough strength, gas retention, and volume in bread and extruded noodles.',
        'health_warnings': ['Processed fat compound containing minor unesterified trans fat fractions.'],
        'contraindications': ['Cardiovascular Disease'],
        'is_disguised_sugar': False
    },
    {
        'code': 'INS 476',
        'aliases': ['E476', '476', 'PGPR', 'Polyglycerol Polyricinoleate'],
        'name': 'Polyglycerol Polyricinoleate',
        'category': 'Emulsifier',
        'risk_level': 'Moderate',
        'description': 'Synthetic castor-oil derived emulsifier used in chocolates to improve flow and replace cocoa butter.',
        'health_warnings': ['Synthetic fat substitute permitted under strict dosage limits.'],
        'contraindications': [],
        'is_disguised_sugar': False
    },
    {
        'code': 'INS 202',
        'aliases': ['E202', '202', 'Potassium Sorbate'],
        'name': 'Potassium Sorbate',
        'category': 'Preservative',
        'risk_level': 'Safe',
        'description': 'Potassium salt of natural sorbic acid preventing yeast and mold spoilage.',
        'health_warnings': ['Generally recognized as safe.'],
        'contraindications': [],
        'is_disguised_sugar': False
    },
    {
        'code': 'INS 223',
        'aliases': ['E223', '223', 'Sodium Metabisulphite'],
        'name': 'Sodium Metabisulphite',
        'category': 'Preservative / Antioxidant',
        'risk_level': 'High',
        'description': 'Sulphite-releasing agent preventing enzymatic discoloration in potato and dough preparations.',
        'health_warnings': ['Triggers severe, potentially life-threatening bronchospasms in sensitive asthmatics.'],
        'contraindications': ['Asthma', 'Sulphite Allergy'],
        'is_disguised_sugar': False
    },
    {
        'code': 'INS 282',
        'aliases': ['E282', '282', 'Calcium Propionate'],
        'name': 'Calcium Propionate',
        'category': 'Preservative',
        'risk_level': 'Low',
        'description': 'Organic calcium salt inhibiting fungal growth in commercial bakery lines.',
        'health_warnings': ['Clinical trials reported behavioral changes, restlessness, and sleep disturbances in children.'],
        'contraindications': ['Paediatric Hyperactivity'],
        'is_disguised_sugar': False
    },
    {
        'code': 'INS 551',
        'aliases': ['E551', '551', 'Silicon Dioxide', 'Silica'],
        'name': 'Silicon Dioxide',
        'category': 'Anti-caking Agent',
        'risk_level': 'Safe',
        'description': 'Inert synthetic amorphous silica added to seasoning powders and spice mixes to prevent caking.',
        'health_warnings': ['Generally recognized as safe at prescribed limits.'],
        'contraindications': [],
        'is_disguised_sugar': False
    }
]

existing_codes = {item['code'].upper() for item in data.get('additives', [])}
for item in new_additives:
    if item['code'].upper() not in existing_codes:
        data['additives'].append(item)
        existing_codes.add(item['code'].upper())

with open(db_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)

print('SUCCESS: Updated data/chemical_db/ins_codes.json with', len(data['additives']), 'additives.')
