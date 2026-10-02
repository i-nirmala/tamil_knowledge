"""
Sample content for the Code Bloom demo knowledge base.

Thirukkural is a ~2,000-year-old classical Tamil text by Thiruvalluvar
and is in the public domain. The English translation used here is
G.U. Pope's 1886 translation, which is also in the public domain.
Explanatory paragraphs are original content written for this project.

This module returns structured "pages" (page_number, text) so the
sample-generation script can render them into a demo PDF using the
same PDF pipeline real users will use for their own documents.
"""

PAGES = [
    # ---------------- Page 1: Cover / Intro ----------------
    {
        "page_number": 1,
        "chapter": "Introduction",
        "text": (
            "திருக்குறள் - Thirukkural\n\n"
            "Thirukkural is a classic Tamil text composed by the poet-philosopher "
            "Thiruvalluvar, believed to have been written around the 1st century BCE "
            "to 5th century CE. It consists of 1,330 short couplets (kurals), organized "
            "into 133 chapters, covering three major themes: Aram (virtue), Porul "
            "(wealth and governance), and Inbam (love).\n\n"
            "This sample knowledge base contains a small curated selection of verses "
            "and explanatory notes covering education, virtue, friendship, and wealth, "
            "provided for demonstration purposes within the Code Bloom project."
        ),
    },
    # ---------------- Page 2: Education (கல்வி) ----------------
    {
        "page_number": 2,
        "chapter": "Kalvi (Education) - Chapter 40",
        "text": (
            "அதிகாரம் 40: கல்வி (The Chapter on Education)\n\n"
            "Kural 391:\n"
            "கற்க கசடறக் கற்பவை கற்றபின்\n"
            "நிற்க அதற்குத் தக.\n"
            "Translation (G.U. Pope): 'Learn thoroughly, without flaw, whatever "
            "you learn; and having learned, live worthy of your learning.'\n\n"
            "Kural 392:\n"
            "கல்லாதவர் நெஞ்சம் கற்றது என ஒக்கும்\n"
            "நல்லாசான் மொழிந்த கருத்து.\n"
            "Translation: The mind of the unlearned, seeking to speak as if learned, "
            "resembles a mimicry of the wise teacher's true insight.\n\n"
            "Explanation: Thiruvalluvar places great emphasis on the importance of "
            "thorough education. According to the Kural, true education is not "
            "merely accumulating information but internalizing it so completely that "
            "one's conduct reflects what has been learned. The teacher (ஆசிரியர்) "
            "plays a central role in shaping a learner's character, not just their "
            "knowledge - the role of the teacher is to guide the student toward "
            "wisdom that is expressed through right action, not simply recited facts."
        ),
    },
    # ---------------- Page 3: Education continued ----------------
    {
        "page_number": 3,
        "chapter": "Kalvi (Education) - Chapter 40 (continued)",
        "text": (
            "Kural 396:\n"
            "தொட்டனைத் தூறும் மணற்கேணி மாந்தர்க்குக்\n"
            "கற்றனைத் தூறும் அறிவு.\n"
            "Translation: As a sand-well, the more it is dug, yields more water, so "
            "the more a person learns, the more their wisdom springs forth.\n\n"
            "Explanation: This verse compares knowledge to an underground spring - "
            "the more effort one invests in learning, the more insight is revealed. "
            "In the context of education, Thiruvalluvar suggests that learning is an "
            "active, continuous process rather than a fixed destination. A teacher's "
            "role, and a student's own diligence, both contribute to how deep this "
            "well of understanding becomes over a lifetime of study."
        ),
    },
    # ---------------- Page 4: Virtue / Ethics ----------------
    {
        "page_number": 4,
        "chapter": "Aram (Virtue) - Chapter 1: Praise of God",
        "text": (
            "அதிகாரம் 1: கடவுள் வாழ்த்து (Praise of God)\n\n"
            "Kural 1:\n"
            "அகர முதல எழுத்தெல்லாம் ஆதி\n"
            "பகவன் முதற்றே உலகு.\n"
            "Translation: As the letter A is the first of all letters, so the "
            "eternal God is first in the world.\n\n"
            "Explanation: The opening verse of Thirukkural establishes the "
            "foundational importance of virtue (aram) by drawing a parallel between "
            "the alphabet's first letter and the primacy of moral and spiritual "
            "grounding in life. Thiruvalluvar's ethical philosophy is often described "
            "as universal and non-sectarian - applicable across faiths and beliefs - "
            "focusing on right conduct as the basis of a meaningful life."
        ),
    },
    # ---------------- Page 5: Friendship ----------------
    {
        "page_number": 5,
        "chapter": "Natpu (Friendship) - Chapter 79",
        "text": (
            "அதிகாரம் 79: நட்பு (Friendship)\n\n"
            "Kural 781:\n"
            "செயற்கரிய யாவுள நட்பின் அதுபோல்\n"
            "வினை மாட்சி இல்லைப் பிற.\n"
            "Translation: There is no virtue greater than friendship; nothing else "
            "achieves such difficult things as true friendship can.\n\n"
            "Explanation: Thiruvalluvar dedicates an entire chapter to the value of "
            "genuine friendship, describing it as a relationship built on honesty, "
            "mutual correction, and shared growth. A true friend, according to the "
            "Kural, is one who points out one's faults for the sake of improvement, "
            "not one who simply flatters."
        ),
    },
    # ---------------- Page 6: Wealth / Governance ----------------
    {
        "page_number": 6,
        "chapter": "Porul (Wealth) - Chapter 76: The Might of Kings",
        "text": (
            "அதிகாரம் 76: படைமாட்சி (The Excellence of an Army / Governance)\n\n"
            "Kural 757:\n"
            "உறுப்பமைந் தூறந்த வெல்படை வேந்தன்\n"
            "வெறுப்பமையா வெல் படை பெரிது.\n"
            "Explanation: In the Porul (wealth/polity) section, Thiruvalluvar "
            "discusses governance, leadership, and statecraft, describing the "
            "qualities of an effective ruler and a well-organized state. These "
            "chapters are often studied by scholars researching classical Tamil "
            "political philosophy and administration."
        ),
    },
]
