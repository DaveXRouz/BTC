"""
Signal Combiner - Synthesis Tier Module
========================================
Purpose: Combine and cross-reference signals from multiple engines
         Planet-Moon combos, Life Path-Personal Year interactions,
         Animal harmony/clash detection, and unified signal prioritization

Dependencies: ReadingEngine output, NumerologyEngine profile, MoonEngine data
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, List


class SignalCombiner:
    """Cross-reference and combine signals from all framework engines."""

    # ----------------------------------------------------------------
    # 1. PLANET_MOON_COMBOS  (7 planets x 8 moon phases = 56 entries)
    # ----------------------------------------------------------------
    PLANET_MOON_COMBOS: Dict[tuple, Dict[str, str]] = {
        # --- Sun ---
        ("Sun", "New Moon"): {
            "theme": "Hidden Potential",
            "message": "Your core identity is being seeded in darkness. Set intentions aligned with your truest self.",
        },
        ("Sun", "Waxing Crescent"): {
            "theme": "Emerging Will",
            "message": "A spark of purpose is catching flame. Feed your confidence with small, deliberate actions.",
        },
        ("Sun", "First Quarter"): {
            "theme": "Identity Tested",
            "message": "Who you are meets who you must become. Resistance now is a forge, not a wall.",
        },
        ("Sun", "Waxing Gibbous"): {
            "theme": "Refining Purpose",
            "message": "Your sense of self is nearly crystallized. Polish the rough edges before the spotlight arrives.",
        },
        ("Sun", "Full Moon"): {
            "theme": "Radiant Revelation",
            "message": "Everything about your identity is illuminated now. Others see you clearly — make sure you see yourself too.",
        },
        ("Sun", "Waning Gibbous"): {
            "theme": "Generous Glow",
            "message": "Your light is warm and giving. Share your confidence — it replenishes by being offered.",
        },
        ("Sun", "Last Quarter"): {
            "theme": "Core Reckoning",
            "message": "Strip away what is performance. The Sun asks what remains when the audience leaves.",
        },
        ("Sun", "Waning Crescent"): {
            "theme": "Quiet Sovereignty",
            "message": "Power rests in stillness now. You do not need to prove your light — it simply is.",
        },
        # --- Moon ---
        ("Moon", "New Moon"): {
            "theme": "Deep Reset",
            "message": "Emotions are in a cocoon. This is not numbness — it is preparation. Honor the silence.",
        },
        ("Moon", "Waxing Crescent"): {
            "theme": "Emotional Seedling",
            "message": "New feelings are tender and fragile. Protect them from harsh judgement — yours or others'.",
        },
        ("Moon", "First Quarter"): {
            "theme": "Feeling the Friction",
            "message": "Emotions push against habit. Let yourself feel the discomfort — it is growth in motion.",
        },
        ("Moon", "Waxing Gibbous"): {
            "theme": "Emotional Refinement",
            "message": "Your inner world is becoming clearer. Journaling or reflection brings surprising insight now.",
        },
        ("Moon", "Full Moon"): {
            "theme": "Emotional Flood",
            "message": "Feelings are at maximum intensity. What surfaces now has been building for weeks. Witness it fully.",
        },
        ("Moon", "Waning Gibbous"): {
            "theme": "Grateful Heart",
            "message": "Emotional abundance flows outward. Gratitude is not just a practice — it is the frequency you carry.",
        },
        ("Moon", "Last Quarter"): {
            "theme": "Emotional Release",
            "message": "Old feelings are ready to be let go. Forgiveness is not forgetting — it is freeing your own heart.",
        },
        ("Moon", "Waning Crescent"): {
            "theme": "Inner Sanctuary",
            "message": "Retreat into the quiet places within. The world can wait while you replenish your emotional reserves.",
        },
        # --- Mars ---
        ("Mars", "New Moon"): {
            "theme": "Coiled Spring",
            "message": "Energy gathers in the dark. Do not strike yet — but sharpen your blade. Timing is everything.",
        },
        ("Mars", "Waxing Crescent"): {
            "theme": "First Strike",
            "message": "The warrior makes the opening move. Start small but start bold. Hesitation is the only enemy.",
        },
        ("Mars", "First Quarter"): {
            "theme": "Battle Decision",
            "message": "Action meets resistance. Push through with courage, not force. The obstacle reveals your true strength.",
        },
        ("Mars", "Waxing Gibbous"): {
            "theme": "Sharpening the Edge",
            "message": "Raw force transforms into precision. Discipline your energy — the battle is almost won through preparation.",
        },
        ("Mars", "Full Moon"): {
            "theme": "Warrior Illuminated",
            "message": "Your drive is fully visible. Channel aggression into passion. Fight for something, not against everything.",
        },
        ("Mars", "Waning Gibbous"): {
            "theme": "Teaching Strength",
            "message": "Your battles have earned you wisdom. Mentor others in courage. Strength shared is strength multiplied.",
        },
        ("Mars", "Last Quarter"): {
            "theme": "Laying Down Arms",
            "message": "Not every hill deserves a fight. Strategic retreat is wisdom, not weakness. Choose your battles.",
        },
        ("Mars", "Waning Crescent"): {
            "theme": "Resting Warrior",
            "message": "Even the fiercest flame needs fuel. Rest now so you may rise again with renewed purpose.",
        },
        # --- Mercury ---
        ("Mercury", "New Moon"): {
            "theme": "Silent Mind",
            "message": "Thoughts incubate in darkness. Do not force clarity — let ideas gestate. The answer forms in quiet.",
        },
        ("Mercury", "Waxing Crescent"): {
            "theme": "First Words",
            "message": "New ideas begin to form. Speak tentatively and listen carefully — the conversation is just beginning.",
        },
        ("Mercury", "First Quarter"): {
            "theme": "Debate Within",
            "message": "Logic clashes with intuition. Both have merit. The resolution lies in listening to both voices.",
        },
        ("Mercury", "Waxing Gibbous"): {
            "theme": "Crafting the Message",
            "message": "Your thoughts are nearly ready for the world. Edit, refine, and clarify before you publish or present.",
        },
        ("Mercury", "Full Moon"): {
            "theme": "Crystal Clarity",
            "message": "Communication peaks. Words land with precision. Important conversations held now carry lasting impact.",
        },
        ("Mercury", "Waning Gibbous"): {
            "theme": "Sharing Knowledge",
            "message": "What you've learned is ready to be taught. Communication flows outward. Write, speak, connect.",
        },
        ("Mercury", "Last Quarter"): {
            "theme": "Revising Thought",
            "message": "Old ideas need updating. Question assumptions that once served you. Mental flexibility is your ally.",
        },
        ("Mercury", "Waning Crescent"): {
            "theme": "Mental Rest",
            "message": "The mind needs sleep as much as the body. Reduce input. Let the subconscious sort what the conscious cannot.",
        },
        # --- Jupiter ---
        ("Jupiter", "New Moon"): {
            "theme": "Seeding Abundance",
            "message": "Plant the seed of a grand vision. Do not worry about the harvest — the soil is rich and waiting.",
        },
        ("Jupiter", "Waxing Crescent"): {
            "theme": "Growing Faith",
            "message": "Optimism stirs. Trust the process even when evidence is scarce. The universe rewards belief backed by action.",
        },
        ("Jupiter", "First Quarter"): {
            "theme": "Expanding Through Challenge",
            "message": "Growth requires discomfort. The expansion you seek is on the other side of this obstacle. Lean in.",
        },
        ("Jupiter", "Waxing Gibbous"): {
            "theme": "Refining Abundance",
            "message": "Wisdom is almost fully formed. Fine-tune your expansion plans before the breakthrough arrives.",
        },
        ("Jupiter", "Full Moon"): {
            "theme": "Harvest of Wisdom",
            "message": "Everything you have learned comes together now. Abundance is not just material — it is understanding made manifest.",
        },
        ("Jupiter", "Waning Gibbous"): {
            "theme": "Philanthropic Flow",
            "message": "Your abundance is meant to circulate. Give generously — not from obligation, but from overflow.",
        },
        ("Jupiter", "Last Quarter"): {
            "theme": "Philosophical Pruning",
            "message": "Not all beliefs serve your growth. Release outdated philosophies that have become cages instead of wings.",
        },
        ("Jupiter", "Waning Crescent"): {
            "theme": "Quiet Gratitude",
            "message": "Before the next expansion, pause to appreciate how far you have come. Gratitude fuels the next cycle.",
        },
        # --- Venus ---
        ("Venus", "New Moon"): {
            "theme": "Love Incubating",
            "message": "Desire stirs beneath the surface. Do not chase — attract. What you value most is taking shape in the unseen.",
        },
        ("Venus", "Waxing Crescent"): {
            "theme": "Beauty Budding",
            "message": "New attractions and creative impulses emerge. Follow what delights you — pleasure is a compass now.",
        },
        ("Venus", "First Quarter"): {
            "theme": "Values Tested",
            "message": "What you love meets what is practical. Compromise does not mean surrender — it means artful integration.",
        },
        ("Venus", "Waxing Gibbous"): {
            "theme": "Perfecting Harmony",
            "message": "Relationships and creative works approach their best form. Small adjustments yield disproportionate beauty.",
        },
        ("Venus", "Full Moon"): {
            "theme": "Love Illuminated",
            "message": "Relationships and values are fully visible. Beauty demands attention. What you love is loving you back.",
        },
        ("Venus", "Waning Gibbous"): {
            "theme": "Graceful Generosity",
            "message": "Share your beauty, your art, your love. The aesthetic gifts you carry are medicine for those around you.",
        },
        ("Venus", "Last Quarter"): {
            "theme": "Releasing Attachment",
            "message": "Love without clinging. Beauty without possession. The heart grows larger when it opens its grip.",
        },
        ("Venus", "Waning Crescent"): {
            "theme": "Self-Love Retreat",
            "message": "Turn the love you give others inward. You cannot pour from an empty cup. Rest in your own beauty.",
        },
        # --- Saturn ---
        ("Saturn", "New Moon"): {
            "theme": "Foundation in Darkness",
            "message": "Discipline begins before anyone is watching. The structures you build now in silence will hold the most weight.",
        },
        ("Saturn", "Waxing Crescent"): {
            "theme": "Early Commitment",
            "message": "The first steps of discipline feel heavy. This is normal. Consistency now creates freedom later.",
        },
        ("Saturn", "First Quarter"): {
            "theme": "Test of Resolve",
            "message": "The structure you are building meets its first real test. Hold firm — the challenge proves the design is sound.",
        },
        ("Saturn", "Waxing Gibbous"): {
            "theme": "Mastering the Details",
            "message": "Discipline matures into craftsmanship. Pay attention to the fine points. Excellence lives in the margins.",
        },
        ("Saturn", "Full Moon"): {
            "theme": "Earned Authority",
            "message": "Your discipline is now visible to all. The respect you receive was built brick by brick. Stand in it fully.",
        },
        ("Saturn", "Waning Gibbous"): {
            "theme": "Elder Wisdom",
            "message": "Your experience is a gift to those still climbing. Teach through example. Mentorship is Saturn's highest calling.",
        },
        ("Saturn", "Last Quarter"): {
            "theme": "Structural Release",
            "message": "Some walls are no longer load-bearing. Identify the rules you follow from habit, not necessity, and let them go.",
        },
        ("Saturn", "Waning Crescent"): {
            "theme": "Final Lesson",
            "message": "The discipline cycle completes. Release what you've outgrown. Rest is not weakness — it is wisdom earned.",
        },
    }

    # ----------------------------------------------------------------
    # 2. LP_PY_COMBOS  (Life Path 1-9 x Personal Year 1-9 = 81 entries)
    # ----------------------------------------------------------------
    LP_PY_COMBOS: Dict[tuple, Dict[str, str]] = {
        # LP 1
        (1, 1): {
            "theme": "Double Ignition",
            "message": "Pioneer entering a year of new beginnings — this is your most powerful launch window. Start what matters most.",
        },
        (1, 2): {
            "theme": "Leader Listens",
            "message": "The Pioneer pauses to build partnerships. Your independence is strengthened, not weakened, by collaboration.",
        },
        (1, 3): {
            "theme": "Creative Spark",
            "message": "The Pioneer finds a voice. Your ideas demand expression now. Write, speak, perform — let originality flow.",
        },
        (1, 4): {
            "theme": "Building the Vision",
            "message": "The Pioneer lays foundations. Your bold ideas need structure. This year rewards planning over impulse.",
        },
        (1, 5): {
            "theme": "Pioneer Unleashed",
            "message": "The Pioneer meets freedom. Every direction calls. Choose the adventure that aligns with your core mission.",
        },
        (1, 6): {
            "theme": "Leader as Guardian",
            "message": "The Pioneer tends to home and heart. Leadership begins with those closest to you. Nurture your roots.",
        },
        (1, 7): {
            "theme": "Solitary Strategy",
            "message": "The Pioneer retreats to plan. Solitude sharpens your vision. The world can wait while you recalibrate.",
        },
        (1, 8): {
            "theme": "Power Surge",
            "message": "The Pioneer steps into authority. Material success and leadership converge. Claim your earned position.",
        },
        (1, 9): {
            "theme": "Pioneer's Completion",
            "message": "The Pioneer reaches an ending. Release old identities so a truer version of yourself can emerge.",
        },
        # LP 2
        (2, 1): {
            "theme": "Diplomat Steps Forward",
            "message": "The Bridge takes the lead for once. Initiate what you have been mediating. Your turn to begin.",
        },
        (2, 2): {
            "theme": "Double Harmony",
            "message": "The Bridge in a year of partnership — your natural gifts peak. Deep connections form effortlessly.",
        },
        (2, 3): {
            "theme": "Harmony Expressed",
            "message": "The Bridge finds creative joy. Your sensitivity becomes art. Express the feelings you usually hold for others.",
        },
        (2, 4): {
            "theme": "Patient Foundation",
            "message": "The Bridge builds slowly and surely. Your patience is your superpower this year. Trust the quiet progress.",
        },
        (2, 5): {
            "theme": "Gentle Adventurer",
            "message": "The Bridge explores new territory. Change feels uncomfortable but necessary. Your adaptability surprises you.",
        },
        (2, 6): {
            "theme": "Heart of Home",
            "message": "The Bridge nurtures deeply. Family and community need your gift for harmony. Love is your primary currency.",
        },
        (2, 7): {
            "theme": "Intuitive Depths",
            "message": "The Bridge turns inward. Your natural sensitivity meets spiritual inquiry. Deep truths surface through meditation.",
        },
        (2, 8): {
            "theme": "Cooperative Power",
            "message": "The Bridge enters the arena of authority. Success comes through alliances, not solo effort. Build your team.",
        },
        (2, 9): {
            "theme": "Releasing Bonds",
            "message": "The Bridge must let some connections go. Completion frees you for deeper, more aligned relationships ahead.",
        },
        # LP 3
        (3, 1): {
            "theme": "Creative Launch",
            "message": "The Voice begins a new project. Your creative vision demands a fresh start. Initiate with joy and boldness.",
        },
        (3, 2): {
            "theme": "Collaborative Art",
            "message": "The Voice finds a duet partner. Creative partnerships flourish. Two imaginations are better than one.",
        },
        (3, 3): {
            "theme": "Triple Expression",
            "message": "The Voice in its power year. Creativity is unstoppable. Every medium calls you. Express without restraint.",
        },
        (3, 4): {
            "theme": "Disciplined Creativity",
            "message": "The Voice learns structure. Your art needs a container. Craft and discipline elevate raw talent into mastery.",
        },
        (3, 5): {
            "theme": "Joyful Exploration",
            "message": "The Voice seeks new audiences. Travel, new social circles, and adventurous expression light up this year.",
        },
        (3, 6): {
            "theme": "Creative Nurturing",
            "message": "The Voice serves family and community. Your words heal. Use your gift of expression to uplift those around you.",
        },
        (3, 7): {
            "theme": "Artist in Solitude",
            "message": "The Voice turns reflective. Your deepest creative work emerges from silence. Seek solitude to find your masterpiece.",
        },
        (3, 8): {
            "theme": "Creative Empire",
            "message": "The Voice builds a platform. Your art meets commerce. This year rewards turning creativity into sustainable success.",
        },
        (3, 9): {
            "theme": "Final Performance",
            "message": "The Voice completes a creative chapter. Share your accumulated wisdom generously. The best art serves others.",
        },
        # LP 4
        (4, 1): {
            "theme": "New Blueprint",
            "message": "The Architect drafts a new plan. Begin the next major structure of your life. Design before you build.",
        },
        (4, 2): {
            "theme": "Building Together",
            "message": "The Architect finds a partner. Collaboration strengthens the foundation. Two sets of hands build faster.",
        },
        (4, 3): {
            "theme": "Playful Structure",
            "message": "The Architect discovers joy in the work. Creativity softens rigidity. Let the building process itself be beautiful.",
        },
        (4, 4): {
            "theme": "Double Foundation",
            "message": "The Architect in their power year. Everything built now has quadruple staying power. Work hard — it all lasts.",
        },
        (4, 5): {
            "theme": "Flexible Framework",
            "message": "The Architect faces disruption. Your structures need to flex, not just hold. Adaptability is the new strength.",
        },
        (4, 6): {
            "theme": "Home Builder",
            "message": "The Architect focuses on domestic foundations. Home, family, and security are the projects that matter most.",
        },
        (4, 7): {
            "theme": "Inner Architecture",
            "message": "The Architect builds within. Spiritual and psychological frameworks need attention. Build the inner temple.",
        },
        (4, 8): {
            "theme": "Material Mastery",
            "message": "The Architect meets material reward. Years of disciplined work pay tangible dividends. Accept the harvest.",
        },
        (4, 9): {
            "theme": "Demolition and Design",
            "message": "The Architect tears down to rebuild. Some structures have served their purpose. Clear the lot for new plans.",
        },
        # LP 5
        (5, 1): {
            "theme": "Adventure Begins",
            "message": "The Explorer launches into unknown territory. A fresh cycle of freedom and discovery opens wide before you.",
        },
        (5, 2): {
            "theme": "Explorer Settles In",
            "message": "The Explorer finds a traveling companion. Freedom is sweeter when shared. Let partnership ground your wanderlust.",
        },
        (5, 3): {
            "theme": "Storyteller's Journey",
            "message": "The Explorer gathers tales. Every experience becomes material for expression. Live fully, then share the story.",
        },
        (5, 4): {
            "theme": "Freedom Meets Form",
            "message": "The Explorer needs a base camp. Freedom without structure scatters energy. Build the launchpad for your next leap.",
        },
        (5, 5): {
            "theme": "Maximum Velocity",
            "message": "The Explorer in peak freedom. Change accelerates from every direction. Ride the wave — do not fight the current.",
        },
        (5, 6): {
            "theme": "Rooted Wanderer",
            "message": "The Explorer comes home. Responsibility calls you back to center. Find adventure within commitment.",
        },
        (5, 7): {
            "theme": "Inner Expedition",
            "message": "The Explorer journeys inward. The most exotic territory is your own consciousness. Meditate, study, question.",
        },
        (5, 8): {
            "theme": "Freedom and Fortune",
            "message": "The Explorer monetizes experience. Your diverse adventures become assets. The world pays for what you know.",
        },
        (5, 9): {
            "theme": "Freedom Through Release",
            "message": "The Explorer reaches a year of completion. Let go of adventures that no longer serve growth. Make room for the next chapter.",
        },
        # LP 6
        (6, 1): {
            "theme": "Guardian's New Chapter",
            "message": "The Guardian begins something for themselves. Self-care is not selfish — it is the foundation of all your giving.",
        },
        (6, 2): {
            "theme": "Deepening Devotion",
            "message": "The Guardian's relationships deepen. Love becomes more nuanced. Partnership thrives through mutual understanding.",
        },
        (6, 3): {
            "theme": "Joyful Service",
            "message": "The Guardian expresses love creatively. Art, beauty, and nurturing merge. Your care becomes an art form.",
        },
        (6, 4): {
            "theme": "Strengthening the Nest",
            "message": "The Guardian fortifies home and family. Practical improvements to your environment bring lasting security.",
        },
        (6, 5): {
            "theme": "Guardian Unchained",
            "message": "The Guardian needs breathing room. Duty and freedom negotiate. Healthy boundaries are acts of love, not betrayal.",
        },
        (6, 6): {
            "theme": "Double Devotion",
            "message": "The Guardian in full power. Love, responsibility, and beauty converge. You are the heart of every room you enter.",
        },
        (6, 7): {
            "theme": "Sacred Service",
            "message": "The Guardian seeks spiritual meaning in duty. Your caregiving becomes a spiritual practice. Find God in the everyday.",
        },
        (6, 8): {
            "theme": "Abundant Caretaker",
            "message": "The Guardian receives material reward for service. Prosperity flows through generosity. Give and receive in equal measure.",
        },
        (6, 9): {
            "theme": "Completing the Circle",
            "message": "The Guardian releases old obligations. Some duties have been fulfilled. Let others carry what you have held too long.",
        },
        # LP 7
        (7, 1): {
            "theme": "Seeker's Fresh Start",
            "message": "The Seeker begins a new inquiry. A question you have never asked before leads you to answers that reshape everything.",
        },
        (7, 2): {
            "theme": "Wisdom in Partnership",
            "message": "The Seeker finds a mirror in another. Deep conversation and emotional intelligence expand your understanding.",
        },
        (7, 3): {
            "theme": "Inner Wisdom Expressed",
            "message": "The Seeker enters a year of creative expression. Your deep insights are ready to be shared. Speak the truth you've found.",
        },
        (7, 4): {
            "theme": "Systematic Discovery",
            "message": "The Seeker builds a method. Your intuitions need a framework. Organize your findings into something teachable.",
        },
        (7, 5): {
            "theme": "Nomadic Philosopher",
            "message": "The Seeker explores through movement. Travel and new experiences crack open old assumptions. Embrace the disruption.",
        },
        (7, 6): {
            "theme": "Wisdom Serves Love",
            "message": "The Seeker applies insight to relationships. Your analytical gifts serve the heart this year. Think less, feel more.",
        },
        (7, 7): {
            "theme": "Double Depth",
            "message": "The Seeker in peak contemplation. Spiritual breakthroughs are possible. Retreat, meditate, and let truth find you.",
        },
        (7, 8): {
            "theme": "Monetized Insight",
            "message": "The Seeker finds material reward for wisdom. Your knowledge has value in the marketplace. Teach, consult, advise.",
        },
        (7, 9): {
            "theme": "Philosopher's Completion",
            "message": "The Seeker finishes a cycle of inquiry. Share your conclusions before beginning the next question.",
        },
        # LP 8
        (8, 1): {
            "theme": "Empire Begins",
            "message": "The Powerhouse launches a new venture. Authority and initiative combine. Build something that outlasts you.",
        },
        (8, 2): {
            "theme": "Strategic Alliance",
            "message": "The Powerhouse partners wisely. True power comes from collaboration. Choose allies whose strengths complement yours.",
        },
        (8, 3): {
            "theme": "Charismatic Authority",
            "message": "The Powerhouse finds a public voice. Leadership meets charm. Your vision inspires others to follow willingly.",
        },
        (8, 4): {
            "theme": "Fortified Empire",
            "message": "The Powerhouse builds infrastructure. Systems, processes, and foundations make the difference between flash and legacy.",
        },
        (8, 5): {
            "theme": "Dynamic Power",
            "message": "The Powerhouse adapts rapidly. Markets shift, circumstances change — your ability to pivot determines your success.",
        },
        (8, 6): {
            "theme": "Benevolent Authority",
            "message": "The Powerhouse serves community. True power is measured by how many you lift, not how high you climb alone.",
        },
        (8, 7): {
            "theme": "Strategic Retreat",
            "message": "The Powerhouse pauses to think deeply. Before the next move, understand the deeper currents. Wisdom precedes action.",
        },
        (8, 8): {
            "theme": "Maximum Authority",
            "message": "The Powerhouse at full capacity. Achievement, recognition, and material mastery converge. Step into your full power.",
        },
        (8, 9): {
            "theme": "Legacy Completion",
            "message": "The Powerhouse finishes a major cycle. What you have built speaks for itself. Release control and let it stand.",
        },
        # LP 9
        (9, 1): {
            "theme": "Sage's New Dawn",
            "message": "The Sage begins again. After completion comes rebirth. Start fresh with all the wisdom of your previous cycles.",
        },
        (9, 2): {
            "theme": "Compassionate Connection",
            "message": "The Sage builds bridges. Your understanding of endings makes you the perfect partner. Share your depth.",
        },
        (9, 3): {
            "theme": "Universal Voice",
            "message": "The Sage speaks for all. Your creative expression carries humanitarian weight. Art as service reaches its zenith.",
        },
        (9, 4): {
            "theme": "Wisdom Made Practical",
            "message": "The Sage grounds the vision. Spiritual insight needs earthly form. Build something tangible from your understanding.",
        },
        (9, 5): {
            "theme": "Sage's Wandering",
            "message": "The Sage explores without attachment. Every experience completes a circle. Move freely and release as you go.",
        },
        (9, 6): {
            "theme": "Healing Presence",
            "message": "The Sage nurtures through wisdom. Your presence alone is medicine. Be with those who need understanding, not fixing.",
        },
        (9, 7): {
            "theme": "Ultimate Contemplation",
            "message": "The Sage meets the mystic. Deepest spiritual insight is available. Seek silence — the answers live there.",
        },
        (9, 8): {
            "theme": "Humanitarian Power",
            "message": "The Sage wields influence for the greater good. Material success serves a higher purpose. Lead with compassion.",
        },
        (9, 9): {
            "theme": "Grand Completion",
            "message": "The Sage completes the ultimate cycle. Everything resolves. Surrender to the ending — the next beginning is already forming.",
        },
    }

    # ----------------------------------------------------------------
    # 3. ANIMAL_HARMONY  (frozenset keys for symmetric lookup)
    # ----------------------------------------------------------------
    ANIMAL_HARMONY: Dict[frozenset, Dict[str, str]] = {
        # --- Traditional Harmonies (6 pairs) ---
        frozenset({"RA", "OX"}): {
            "type": "harmony",
            "meaning": "Resourcefulness meets endurance. Together these energies create unstoppable momentum through patience and perception.",
        },
        frozenset({"TI", "PI"}): {
            "type": "harmony",
            "meaning": "Courage meets generosity. The bold tiger finds softness in the pig's abundance, creating noble strength.",
        },
        frozenset({"RU", "DO"}): {
            "type": "harmony",
            "meaning": "Intuition meets loyalty. The rabbit's gentle instinct paired with the dog's devotion creates trustworthy guidance.",
        },
        frozenset({"DR", "RO"}): {
            "type": "harmony",
            "meaning": "Transformation meets truth. The dragon's destiny and the rooster's honesty forge a path of authentic power.",
        },
        frozenset({"SN", "MO"}): {
            "type": "harmony",
            "meaning": "Wisdom meets cleverness. The snake's depth and the monkey's agility create brilliant strategic insight.",
        },
        frozenset({"HO", "GO"}): {
            "type": "harmony",
            "meaning": "Freedom meets creativity. The horse's passionate movement and the goat's artistic vision produce inspired action.",
        },
        # --- Traditional Clashes (6 pairs) ---
        frozenset({"RA", "HO"}): {
            "type": "clash",
            "meaning": "Cunning perception clashes with unbridled freedom. One calculates while the other charges forward without looking.",
        },
        frozenset({"OX", "GO"}): {
            "type": "clash",
            "meaning": "Stubborn endurance meets sensitive artistry. Rigidity and fluidity struggle to find common ground.",
        },
        frozenset({"TI", "MO"}): {
            "type": "clash",
            "meaning": "Bold authority confronts clever defiance. Power and trickery create friction that demands resolution.",
        },
        frozenset({"RU", "RO"}): {
            "type": "clash",
            "meaning": "Gentle diplomacy versus blunt truth. The rabbit's softness feels wounded by the rooster's sharp honesty.",
        },
        frozenset({"DR", "DO"}): {
            "type": "clash",
            "meaning": "Grand destiny meets grounded loyalty. The dragon's ambition feels constrained by the dog's call to duty.",
        },
        frozenset({"SN", "PI"}): {
            "type": "clash",
            "meaning": "Deep precision meets open generosity. The snake's calculated nature distrusts the pig's unconditional giving.",
        },
        # --- Resonance pairs (same animal) ---
        frozenset({"RA"}): {
            "type": "resonance",
            "meaning": "Double Rat amplifies resourcefulness and sharp perception. Hyper-awareness — trust your instincts completely.",
        },
        frozenset({"OX"}): {
            "type": "resonance",
            "meaning": "Double Ox amplifies endurance and determination. Immovable resolve — nothing can shake your foundation today.",
        },
        frozenset({"TI"}): {
            "type": "resonance",
            "meaning": "Double Tiger amplifies courage and boldness. Fearless energy — but beware of recklessness in the intensity.",
        },
        frozenset({"RU"}): {
            "type": "resonance",
            "meaning": "Double Rabbit amplifies intuition and sensitivity. Deep knowing flows through you — listen to the whispers.",
        },
        frozenset({"DR"}): {
            "type": "resonance",
            "meaning": "Double Dragon amplifies transformation and destiny. Monumental shifts are underway — embrace the magnitude.",
        },
        frozenset({"SN"}): {
            "type": "resonance",
            "meaning": "Double Snake amplifies wisdom and precision. Penetrating insight — you see what others cannot.",
        },
        frozenset({"HO"}): {
            "type": "resonance",
            "meaning": "Double Horse amplifies freedom and passionate energy. Unstoppable movement — but remember where home is.",
        },
        frozenset({"GO"}): {
            "type": "resonance",
            "meaning": "Double Goat amplifies creativity and artistic vision. Beauty saturates everything — let yourself be moved.",
        },
        frozenset({"MO"}): {
            "type": "resonance",
            "meaning": "Double Monkey amplifies adaptability and wit. Quick thinking dominates — use your cleverness wisely.",
        },
        frozenset({"RO"}): {
            "type": "resonance",
            "meaning": "Double Rooster amplifies truth and discipline. Absolute clarity — speak with confidence and precision.",
        },
        frozenset({"DO"}): {
            "type": "resonance",
            "meaning": "Double Dog amplifies loyalty and protection. Fierce devotion — guard what matters most with everything you have.",
        },
        frozenset({"PI"}): {
            "type": "resonance",
            "meaning": "Double Pig amplifies abundance and generosity. Overflowing warmth — share freely without fear of scarcity.",
        },
        # --- Notable neutral pairs ---
        frozenset({"RA", "DR"}): {
            "type": "neutral",
            "meaning": "Rat and Dragon coexist with mutual respect. Resourcefulness acknowledges destiny without interference.",
        },
        frozenset({"OX", "SN"}): {
            "type": "neutral",
            "meaning": "Ox and Snake find quiet companionship. Both value patience and depth, operating on parallel tracks.",
        },
        frozenset({"TI", "HO"}): {
            "type": "neutral",
            "meaning": "Tiger and Horse share energetic independence. Both need freedom but express it through different channels.",
        },
        frozenset({"RU", "GO"}): {
            "type": "neutral",
            "meaning": "Rabbit and Goat share artistic sensitivity. Both appreciate beauty, creating a gentle, aesthetic atmosphere.",
        },
        frozenset({"MO", "DR"}): {
            "type": "neutral",
            "meaning": "Monkey and Dragon share ambition without conflict. Cleverness serves destiny in a productive alliance.",
        },
        frozenset({"RO", "SN"}): {
            "type": "neutral",
            "meaning": "Rooster and Snake share analytical precision. Both value truth, though they seek it through different methods.",
        },
        frozenset({"DO", "TI"}): {
            "type": "neutral",
            "meaning": "Dog and Tiger share a sense of justice. Both protect the vulnerable, though their methods differ.",
        },
        frozenset({"PI", "RU"}): {
            "type": "neutral",
            "meaning": "Pig and Rabbit share gentle warmth. Both value comfort and kindness, creating a peaceful environment.",
        },
    }

    # Priority hierarchy for signal sorting
    PRIORITY_RANK: Dict[str, int] = {
        "Very High": 6,
        "High": 5,
        "Medium": 4,
        "Low-Medium": 3,
        "Low": 2,
        "Background": 1,
    }

    # Element clash pairs
    ELEMENT_CLASHES: Dict[frozenset, str] = {
        frozenset(
            {"Fire", "Water"}
        ): "Fire and Water oppose — passion and depth struggle for dominance.",
        frozenset(
            {"Wood", "Metal"}
        ): "Wood and Metal oppose — growth meets cutting refinement.",
        frozenset(
            {"FI", "WA"}
        ): "Fire and Water oppose — passion and depth struggle for dominance.",
        frozenset(
            {"WU", "MT"}
        ): "Wood and Metal oppose — growth meets cutting refinement.",
    }

    @staticmethod
    def planet_meets_moon(planet: str, moon_phase: str) -> Dict[str, str]:
        """
        Look up the combined meaning of a planet-day and moon-phase.

        Args:
            planet: One of Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn
            moon_phase: One of the 8 standard moon phase names

        Returns:
            Dict with 'theme' and 'message' keys
        """
        result = SignalCombiner.PLANET_MOON_COMBOS.get((planet, moon_phase))
        if result:
            return dict(result)
        return {
            "theme": "Uncharted Alignment",
            "message": f"The combination of {planet} and {moon_phase} is rare and personal. Observe what arises without expectation.",
        }

    @staticmethod
    def lifepath_meets_year(life_path: int, personal_year: int) -> Dict[str, str]:
        """
        Look up the combined meaning of Life Path and Personal Year.

        Master numbers (11, 22, 33) first check direct lookup, then
        fall back to their reduced form with an amplification note.

        Args:
            life_path: Life Path number (1-9, or master: 11, 22, 33)
            personal_year: Personal Year number (1-9, or master: 11, 22, 33)

        Returns:
            Dict with 'theme' and 'message' keys
        """
        master_reduction = {11: 2, 22: 4, 33: 6}

        # Direct lookup first
        result = SignalCombiner.LP_PY_COMBOS.get((life_path, personal_year))
        if result:
            return dict(result)

        # Try reducing master numbers
        lp_reduced = master_reduction.get(life_path, life_path)
        py_reduced = master_reduction.get(personal_year, personal_year)
        original_lp = life_path

        result = SignalCombiner.LP_PY_COMBOS.get((lp_reduced, py_reduced))
        if result:
            out = dict(result)
            if life_path in master_reduction:
                out["message"] += f" (amplified by Master Number {original_lp})"
            if personal_year in master_reduction:
                out["message"] += f" (amplified by Master Year {personal_year})"
            return out

        return {
            "theme": "Unique Intersection",
            "message": f"Life Path {life_path} meets Personal Year {personal_year}. This combination invites personal interpretation.",
        }

    @staticmethod
    def animal_harmony(animal1: str, animal2: str) -> Dict[str, str]:
        """
        Determine the harmony relationship between two animal tokens.

        Symmetric — animal_harmony("RA", "OX") == animal_harmony("OX", "RA").
        Same animal returns resonance type.

        Args:
            animal1: 2-char animal token (e.g. "RA", "OX")
            animal2: 2-char animal token

        Returns:
            Dict with 'type' (harmony/clash/resonance/neutral) and 'meaning'
        """
        key = frozenset({animal1, animal2})
        result = SignalCombiner.ANIMAL_HARMONY.get(key)
        if result:
            return dict(result)
        return {
            "type": "neutral",
            "meaning": "These energies coexist without strong interaction.",
        }

    @staticmethod
    def _detect_tensions(signals: List[Dict], ganzhi: Dict) -> List[str]:
        """Detect conflicting energies in signal data."""
        tensions = []

        # Collect elements from signals
        elements_found = []
        for s in signals:
            msg = s.get("message", "").lower()
            for el_name in ("fire", "water", "wood", "metal", "earth"):
                if el_name in msg:
                    elements_found.append(el_name.capitalize())

        # Check element clashes
        seen_elements = set(elements_found)
        for clash_pair, description in SignalCombiner.ELEMENT_CLASHES.items():
            if clash_pair.issubset(seen_elements):
                tensions.append(description)

        # Check animal clashes from ganzhi data
        animals_in_play = []
        if ganzhi:
            for period in ("year", "day", "hour"):
                branch = ganzhi.get(period, {}).get("branch_token", "")
                if branch:
                    animals_in_play.append(branch)

        for i in range(len(animals_in_play)):
            for j in range(i + 1, len(animals_in_play)):
                pair_result = SignalCombiner.animal_harmony(
                    animals_in_play[i], animals_in_play[j]
                )
                if pair_result["type"] == "clash":
                    tensions.append(pair_result["meaning"])

        return tensions

    @staticmethod
    def _generate_actions(
        signals: List[Dict], numerology: Dict, moon: Dict
    ) -> List[str]:
        """Generate 3 recommended actions based on the strongest signals."""
        actions = []

        # Action from strongest signal
        if signals:
            top = signals[0]
            msg = top.get("message", "")
            if "repetition" in top.get("type", "") or "animal" in top.get("type", ""):
                actions.append(
                    "Pay attention to the repeated pattern — it is the loudest signal. Align your actions with its energy."
                )
            elif "planet" in top.get("type", ""):
                actions.append(
                    f"Lean into today's planetary theme. {msg.split('.')[0]}."
                )
            elif "moon" in top.get("type", ""):
                actions.append(
                    "Follow the moon's guidance for timing. Work with the lunar rhythm, not against it."
                )
            else:
                actions.append(
                    "Focus on the primary signal of the moment. Let it guide your first decision today."
                )

        # Action from numerology
        if numerology:
            py = numerology.get("personal_year", 0)
            lp_info = numerology.get("life_path", {})
            lp_msg = lp_info.get("message", "")
            if lp_msg:
                actions.append(
                    f"Your Life Path asks you to {lp_msg.lower()}. Let Personal Year {py} shape how you approach it."
                )

        # Action from moon
        if moon:
            best_for = moon.get("best_for", "")
            if best_for:
                actions.append(
                    f"The moon says this time is best for: {best_for.lower()}. Schedule accordingly."
                )

        # Ensure we have at least 3 actions
        defaults = [
            "Observe the patterns around you before making major decisions.",
            "Journal about what feels resonant today — the signals are personal.",
            "Take one small action aligned with the strongest energy you feel.",
        ]
        while len(actions) < 3:
            actions.append(defaults[len(actions) % len(defaults)])

        return actions[:3]

    @staticmethod
    def combine_signals(
        signals: List[Dict],
        numerology: Dict,
        moon: Dict,
        ganzhi: Dict,
    ) -> Dict:
        """
        Combine and prioritize signals from all engines.

        Args:
            signals: List of signal dicts from ReadingEngine
                     (each has 'type', 'priority', 'message')
            numerology: Output from NumerologyEngine.complete_profile()
            moon: Output from MoonEngine.full_moon_info()
            ganzhi: Dict with 'year', 'day', 'hour' ganzhi info

        Returns:
            Dict with primary_message, supporting_messages,
            tensions, and recommended_actions
        """
        rank = SignalCombiner.PRIORITY_RANK

        # Sort signals by priority (highest first)
        sorted_signals = sorted(
            signals,
            key=lambda s: rank.get(s.get("priority", ""), 0),
            reverse=True,
        )

        # Primary message from highest priority signal
        primary_message = ""
        if sorted_signals:
            primary_message = sorted_signals[0].get("message", "")

        # Supporting messages from next 2-3 signals
        supporting_messages = []
        for s in sorted_signals[1:4]:
            supporting_messages.append(s.get("message", ""))

        # Detect tensions
        tensions = SignalCombiner._detect_tensions(sorted_signals, ganzhi)

        # Generate recommended actions
        recommended_actions = SignalCombiner._generate_actions(
            sorted_signals, numerology, moon
        )

        return {
            "primary_message": primary_message,
            "supporting_messages": supporting_messages,
            "tensions": tensions,
            "recommended_actions": recommended_actions,
        }


if __name__ == "__main__":
    print("=" * 60)
    print("SIGNAL COMBINER - SELF TEST")
    print("=" * 60)

    passed = 0
    failed = 0

    # Test 1: All 56 planet x moon combos return non-empty theme and message
    planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    phases = [
        "New Moon",
        "Waxing Crescent",
        "First Quarter",
        "Waxing Gibbous",
        "Full Moon",
        "Waning Gibbous",
        "Last Quarter",
        "Waning Crescent",
    ]
    all_pm_ok = True
    for p in planets:
        for ph in phases:
            result = SignalCombiner.planet_meets_moon(p, ph)
            if not result.get("theme") or not result.get("message"):
                all_pm_ok = False
                print(f"  MISSING: ({p}, {ph})")
    if all_pm_ok and len(SignalCombiner.PLANET_MOON_COMBOS) == 56:
        print(f"PASS [1] All 56 planet x moon combos have theme and message")
        passed += 1
    else:
        print(
            f"FAIL [1] Planet x moon combos: count={len(SignalCombiner.PLANET_MOON_COMBOS)}, all_ok={all_pm_ok}"
        )
        failed += 1

    # Test 2: All 81 LP x PY combos return non-empty theme and message
    all_lp_ok = True
    for lp in range(1, 10):
        for py in range(1, 10):
            result = SignalCombiner.lifepath_meets_year(lp, py)
            if not result.get("theme") or not result.get("message"):
                all_lp_ok = False
                print(f"  MISSING: ({lp}, {py})")
    if all_lp_ok and len(SignalCombiner.LP_PY_COMBOS) == 81:
        print(f"PASS [2] All 81 LP x PY combos have theme and message")
        passed += 1
    else:
        print(
            f"FAIL [2] LP x PY combos: count={len(SignalCombiner.LP_PY_COMBOS)}, all_ok={all_lp_ok}"
        )
        failed += 1

    # Test 3: planet_meets_moon("Sun", "Full Moon") returns expected theme
    r = SignalCombiner.planet_meets_moon("Sun", "Full Moon")
    if r["theme"] == "Radiant Revelation":
        print(f"PASS [3] Sun + Full Moon = '{r['theme']}'")
        passed += 1
    else:
        print(
            f"FAIL [3] Sun + Full Moon = '{r['theme']}' (expected 'Radiant Revelation')"
        )
        failed += 1

    # Test 4: lifepath_meets_year(1, 1) returns expected theme
    r = SignalCombiner.lifepath_meets_year(1, 1)
    if r["theme"] == "Double Ignition":
        print(f"PASS [4] LP1 + PY1 = '{r['theme']}'")
        passed += 1
    else:
        print(f"FAIL [4] LP1 + PY1 = '{r['theme']}' (expected 'Double Ignition')")
        failed += 1

    # Test 5: animal_harmony("RA", "OX") returns "harmony" type
    r = SignalCombiner.animal_harmony("RA", "OX")
    if r["type"] == "harmony":
        print(f"PASS [5] RA + OX = '{r['type']}'")
        passed += 1
    else:
        print(f"FAIL [5] RA + OX = '{r['type']}' (expected 'harmony')")
        failed += 1

    # Test 6: animal_harmony("RA", "HO") returns "clash" type
    r = SignalCombiner.animal_harmony("RA", "HO")
    if r["type"] == "clash":
        print(f"PASS [6] RA + HO = '{r['type']}'")
        passed += 1
    else:
        print(f"FAIL [6] RA + HO = '{r['type']}' (expected 'clash')")
        failed += 1

    # Test 7: Symmetry — animal_harmony("OX", "RA") == animal_harmony("RA", "OX")
    r1 = SignalCombiner.animal_harmony("OX", "RA")
    r2 = SignalCombiner.animal_harmony("RA", "OX")
    if r1 == r2:
        print(
            f"PASS [7] Symmetry: animal_harmony('OX','RA') == animal_harmony('RA','OX')"
        )
        passed += 1
    else:
        print(f"FAIL [7] Symmetry broken: {r1} != {r2}")
        failed += 1

    # Test 8: animal_harmony("RA", "RA") returns "resonance" type
    r = SignalCombiner.animal_harmony("RA", "RA")
    if r["type"] == "resonance":
        print(f"PASS [8] RA + RA = '{r['type']}'")
        passed += 1
    else:
        print(f"FAIL [8] RA + RA = '{r['type']}' (expected 'resonance')")
        failed += 1

    # Test 9: combine_signals with test data returns expected structure
    test_signals = [
        {
            "type": "animal_repetition",
            "priority": "Very High",
            "message": "Ox appears 3 times — endurance is key.",
        },
        {
            "type": "day_planet",
            "priority": "Medium",
            "message": "This is a Venus day, governing love and beauty.",
        },
        {
            "type": "moon_phase",
            "priority": "Medium",
            "message": "Waning Gibbous — share what you have learned.",
        },
        {
            "type": "hour_animal",
            "priority": "Low-Medium",
            "message": "The Tiger hour carries courage.",
        },
    ]
    test_numerology = {
        "life_path": {"number": 5, "title": "Explorer", "message": "Change and adapt"},
        "personal_year": 9,
    }
    test_moon = {"best_for": "reflection and release"}
    test_ganzhi = {}
    combined = SignalCombiner.combine_signals(
        test_signals, test_numerology, test_moon, test_ganzhi
    )
    has_keys = all(
        k in combined
        for k in (
            "primary_message",
            "supporting_messages",
            "tensions",
            "recommended_actions",
        )
    )
    correct_primary = "Ox appears 3 times" in combined["primary_message"]
    has_3_actions = len(combined["recommended_actions"]) == 3
    if has_keys and correct_primary and has_3_actions:
        print(
            f"PASS [9] combine_signals returns correct structure with primary='Ox...' and 3 actions"
        )
        passed += 1
    else:
        print(
            f"FAIL [9] combine_signals: keys={has_keys}, primary={correct_primary}, actions={has_3_actions}"
        )
        failed += 1

    # Test 10: lifepath_meets_year(11, 5) falls back to (2, 5) with master modifier
    r = SignalCombiner.lifepath_meets_year(11, 5)
    is_fallback_theme = r["theme"] == SignalCombiner.LP_PY_COMBOS[(2, 5)]["theme"]
    has_master_note = "Master Number 11" in r["message"]
    if is_fallback_theme and has_master_note:
        print(
            f"PASS [10] LP11 + PY5 falls back to LP2+PY5 with master modifier: '{r['theme']}'"
        )
        passed += 1
    else:
        print(
            f"FAIL [10] LP11+PY5: theme_match={is_fallback_theme}, master_note={has_master_note}, msg='{r['message']}'"
        )
        failed += 1

    print(f"\n{passed} passed, {failed} failed")
    exit(0 if failed == 0 else 1)
