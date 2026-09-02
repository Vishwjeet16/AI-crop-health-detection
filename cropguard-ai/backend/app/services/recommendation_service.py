"""
Recommendation engine.

Deliberately template-based rather than LLM-generated: every action here is
a static, reviewed string. This is what section 33 of the spec means by
"never invent pesticide names, doses, or chemical concentrations" — the
templates below give general IPM-aligned guidance and explicitly defer
chemical-control decisions to verified sources (ICAR / KVK / state
agriculture departments). Swap or extend TEMPLATES with content reviewed by
an agricultural domain expert before this goes anywhere near production.

Keys here must line up with the `class_` values used in
app/services/demo_outcomes.py (and, later, whatever class names the real
YOLO model emits) — get_recommendation() falls back to a generic template
for anything unmapped, but that fallback should be the exception, not the
default, once a new crop/disease is added.
"""

from app.schemas.scans import Recommendation

DEFAULT_NEXT_SCAN = "Recommended monitoring: rescan according to crop-specific guidance."

TEMPLATES: dict[str, Recommendation] = {
    "early_blight": Recommendation(
        title="Inspect affected plants",
        actions=[
            "Inspect nearby plants and remove severely affected plant material where appropriate.",
            "Continue monitoring the field over the next few days.",
        ],
        prevention=[
            "Maintain field hygiene.",
            "Monitor nearby plants.",
            "Avoid unnecessary irrigation.",
            "Follow local agricultural guidance.",
        ],
        next_scan=DEFAULT_NEXT_SCAN,
    ),
    "late_blight": Recommendation(
        title="Act promptly — fast-spreading disease",
        actions=[
            "Late blight can spread quickly in humid conditions — inspect the whole field, not just the scanned plant.",
            "Remove and safely dispose of severely affected plant material away from the field.",
            "Avoid overhead irrigation and working in the field while foliage is wet, which can spread spores.",
        ],
        prevention=[
            "Improve airflow between plants where possible.",
            "Avoid unnecessary irrigation, especially in the evening.",
            "Follow local agricultural guidance for fungicide timing.",
        ],
        next_scan="Given the severity, consider rescanning within 2-3 days rather than waiting for the usual interval.",
    ),
    "leaf_curl": Recommendation(
        title="Monitor for pest activity",
        actions=[
            "Check the underside of leaves for whiteflies or aphids, common leaf-curl vectors.",
            "Isolate or mark affected plants for closer monitoring.",
        ],
        prevention=[
            "Maintain field hygiene.",
            "Avoid excess nitrogen fertilizer, which can worsen symptoms.",
            "Follow local agricultural guidance for vector control.",
        ],
        next_scan=DEFAULT_NEXT_SCAN,
    ),
    "bollworm_damage": Recommendation(
        title="Inspect bolls and nearby plants",
        actions=[
            "Check nearby bolls and squares for entry holes or larvae.",
            "Consider pheromone traps to monitor moth activity, if available locally.",
        ],
        prevention=[
            "Maintain field hygiene and remove crop residue after harvest.",
            "Monitor field margins, where infestations often start.",
            "Follow local agricultural guidance for integrated pest management.",
        ],
        next_scan=DEFAULT_NEXT_SCAN,
    ),
    "soybean_rust": Recommendation(
        title="Inspect lower canopy leaves",
        actions=[
            "Rust often starts in the lower canopy — check leaves low on the plant, not just the top.",
            "Continue monitoring the field over the next few days.",
        ],
        prevention=[
            "Maintain field hygiene.",
            "Avoid dense planting where possible, to improve airflow.",
            "Follow local agricultural guidance.",
        ],
        next_scan=DEFAULT_NEXT_SCAN,
    ),
    "wheat_rust": Recommendation(
        title="Inspect stems and leaves across the field",
        actions=[
            "Check multiple plants across the field — rust can spread unevenly.",
            "Continue monitoring, especially if conditions stay humid.",
        ],
        prevention=[
            "Maintain field hygiene.",
            "Consider rust-resistant varieties for future planting where feasible.",
            "Follow local agricultural guidance.",
        ],
        next_scan=DEFAULT_NEXT_SCAN,
    ),
    "rice_blast": Recommendation(
        title="Inspect leaves and neck nodes",
        actions=[
            "Check both leaves and neck/panicle nodes — blast can affect either.",
            "Avoid excess nitrogen application until the field is reassessed.",
        ],
        prevention=[
            "Maintain proper water management — avoid prolonged drought stress.",
            "Maintain field hygiene.",
            "Follow local agricultural guidance.",
        ],
        next_scan=DEFAULT_NEXT_SCAN,
    ),
    # --- Classes the PlantDoc-trained detector can emit (see
    # ml/training/data.yaml). Names must match that file's `names` exactly. ---
    "bacterial_spot": Recommendation(
        title="Reduce leaf wetness and handling",
        actions=[
            "Bacterial spot spreads in splashing water — avoid overhead irrigation and "
            "avoid working among plants while the foliage is wet.",
            "Remove and safely dispose of severely affected leaves away from the field.",
        ],
        prevention=[
            "Use clean, certified seed or healthy transplants for the next planting.",
            "Rotate away from tomato, chilli, and capsicum in affected plots where possible.",
            "Maintain field hygiene and remove crop residue after harvest.",
            "Follow local agricultural guidance for any chemical control.",
        ],
        next_scan=DEFAULT_NEXT_SCAN,
    ),
    "septoria_leaf_spot": Recommendation(
        title="Check the lower canopy first",
        actions=[
            "Septoria usually starts on the oldest, lowest leaves — inspect the bottom of "
            "the plant, not just the top growth.",
            "Remove and safely dispose of the worst affected lower leaves.",
        ],
        prevention=[
            "Mulch around the base to reduce soil splashing onto leaves.",
            "Stake or space plants to improve airflow and let foliage dry faster.",
            "Rotate crops and remove residue after harvest.",
            "Follow local agricultural guidance.",
        ],
        next_scan=DEFAULT_NEXT_SCAN,
    ),
    "leaf_mold": Recommendation(
        title="Lower the humidity around the plants",
        actions=[
            "Leaf mold thrives in prolonged high humidity — improve ventilation, especially "
            "inside polyhouses or tunnels.",
            "Remove and safely dispose of affected leaves away from the field.",
        ],
        prevention=[
            "Space plants and prune to improve airflow.",
            "Water at the base rather than over the canopy, and water early in the day.",
            "Follow local agricultural guidance.",
        ],
        next_scan=DEFAULT_NEXT_SCAN,
    ),
    "mosaic_virus": Recommendation(
        title="Isolate affected plants — this virus spreads by handling",
        actions=[
            "There is no cure for an infected plant. Mark or remove affected plants and "
            "dispose of them away from the field — do not compost them.",
            "Wash hands and clean tools between plants, and handle affected plants last.",
        ],
        prevention=[
            "Avoid tobacco use while working with the crop — it can carry related viruses.",
            "Control sap-feeding insects, which can move some mosaic viruses between plants.",
            "Consider resistant varieties for the next planting.",
            "Follow local agricultural guidance.",
        ],
        next_scan="Rescan the surrounding plants within a week to catch further spread early.",
    ),
    "powdery_mildew": Recommendation(
        title="Improve airflow and monitor spread",
        actions=[
            "Check both leaf surfaces — powdery mildew often coats the upper side first.",
            "Remove and safely dispose of severely affected leaves to slow spread.",
        ],
        prevention=[
            "Space plants and remove excess growth so air moves through the canopy.",
            "Avoid excess nitrogen fertilizer, which encourages susceptible soft growth.",
            "Consider resistant varieties for the next planting.",
            "Follow local agricultural guidance for fungicide timing.",
        ],
        next_scan=DEFAULT_NEXT_SCAN,
    ),
    "corn_leaf_blight": Recommendation(
        title="Assess how much leaf area is affected",
        actions=[
            "Check whether lesions are reaching the leaves above the ear — that is where "
            "leaf loss costs the most yield.",
            "Inspect several plants across the field, as spread is often uneven.",
        ],
        prevention=[
            "Rotate away from maize and manage crop residue, which carries the fungus over.",
            "Consider resistant hybrids for the next season.",
            "Follow local agricultural guidance for fungicide timing.",
        ],
        next_scan=DEFAULT_NEXT_SCAN,
    ),
    "corn_rust": Recommendation(
        title="Monitor — usually less damaging than blight",
        actions=[
            "Check both leaf surfaces for pustules, and note how far up the plant they reach.",
            "Keep monitoring while conditions stay cool and humid.",
        ],
        prevention=[
            "Consider resistant hybrids for the next season.",
            "Maintain field hygiene.",
            "Follow local agricultural guidance.",
        ],
        next_scan=DEFAULT_NEXT_SCAN,
    ),
    "gray_leaf_spot": Recommendation(
        title="Check residue management and airflow",
        actions=[
            "Look for rectangular lesions running along the leaf veins, and check how many "
            "leaves above the ear are affected.",
            "Inspect multiple plants across the field before deciding on action.",
        ],
        prevention=[
            "Rotate away from continuous maize — surface residue is the main carryover source.",
            "Incorporate or manage residue where local practice allows.",
            "Consider resistant hybrids for the next season.",
            "Follow local agricultural guidance.",
        ],
        next_scan=DEFAULT_NEXT_SCAN,
    ),
    "apple_rust": Recommendation(
        title="Inspect leaves and look for nearby host trees",
        actions=[
            "Check leaves for orange-yellow spots, and inspect fruit and young shoots too.",
            "Look for juniper or cedar trees nearby — this rust needs them to complete its cycle.",
        ],
        prevention=[
            "Remove galls from nearby juniper/cedar where that is feasible and permitted.",
            "Consider resistant cultivars for new planting.",
            "Follow local agricultural guidance for spray timing during wet spring weather.",
        ],
        next_scan=DEFAULT_NEXT_SCAN,
    ),
    "apple_scab": Recommendation(
        title="Clear leaf litter and improve drying",
        actions=[
            "Check leaves and developing fruit for olive-green to dark scabby lesions.",
            "Rake up and remove fallen leaves, which is where the fungus overwinters.",
        ],
        prevention=[
            "Prune to open the canopy so leaves and fruit dry faster after rain.",
            "Consider scab-resistant cultivars for new planting.",
            "Follow local agricultural guidance for spray timing during wet spring weather.",
        ],
        next_scan=DEFAULT_NEXT_SCAN,
    ),
    "black_rot": Recommendation(
        title="Remove mummified fruit and infected wood",
        actions=[
            "Look for dried, shrivelled 'mummy' berries and dark lesions on canes — these "
            "carry the infection into the next season.",
            "Prune out and remove infected canes and mummies from the vineyard.",
        ],
        prevention=[
            "Keep the canopy open so clusters and leaves dry quickly after rain.",
            "Remove fallen fruit and prunings rather than leaving them under the vines.",
            "Follow local agricultural guidance for spray timing in wet spring conditions.",
        ],
        next_scan=DEFAULT_NEXT_SCAN,
    ),
    "spider_mite_damage": Recommendation(
        title="Check leaf undersides for mites",
        actions=[
            "Look on the underside of leaves for fine webbing and tiny moving specks; "
            "stippled, bronzed leaves are the usual first sign.",
            "A firm spray of water on leaf undersides can knock populations back.",
        ],
        prevention=[
            "Keep plants adequately watered — mites build up fastest on dust-stressed, dry plants.",
            "Reduce dust on foliage along field edges and paths.",
            "Avoid broad-spectrum sprays that kill the predatory mites and insects already "
            "holding the population down.",
            "Follow local agricultural guidance.",
        ],
        next_scan="Mite populations build quickly in hot, dry weather — rescan within a week.",
    ),
    "healthy": Recommendation(
        title="No action needed",
        actions=["Continue routine monitoring."],
        prevention=["Maintain field hygiene.", "Keep scanning regularly."],
        next_scan=DEFAULT_NEXT_SCAN,
    ),
    "low_confidence": Recommendation(
        title="Re-scan recommended",
        actions=[
            "The AI is not confident enough to identify an issue from this image.",
            "Capture a clearer, well-lit photo focused on the affected area, or consult an agricultural expert.",
        ],
        prevention=["Maintain field hygiene.", "Keep scanning regularly."],
        next_scan=DEFAULT_NEXT_SCAN,
    ),
    # Safety net for a detection class with no template of its own. Naming a
    # specific disease here would be worse than saying nothing: the previous
    # implementation fell back to the early_blight template, so any unmapped
    # class was presented to the farmer as early blight.
    "unknown": Recommendation(
        title="Issue detected — identification unconfirmed",
        actions=[
            "Something was detected on this plant, but it does not match a condition this "
            "app has reviewed guidance for.",
            "Inspect nearby plants for the same symptoms and note how far it has spread.",
            "Show this photo to your local KVK or agriculture extension officer before "
            "treating.",
        ],
        prevention=[
            "Maintain field hygiene.",
            "Avoid moving soil, tools, or plant material from the affected area to clean areas.",
            "Follow local agricultural guidance.",
        ],
        next_scan=DEFAULT_NEXT_SCAN,
    ),
}


def get_recommendation(detection_class: str | None, confidence: float | None) -> Recommendation:
    if detection_class is None:
        return TEMPLATES["healthy"]
    if confidence is not None and confidence < 0.6:
        return TEMPLATES["low_confidence"]
    return TEMPLATES.get(detection_class, TEMPLATES["unknown"])
