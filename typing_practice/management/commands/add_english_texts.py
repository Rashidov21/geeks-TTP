from django.core.management.base import BaseCommand
from typing_practice.models import Text
import random
import string


class Command(BaseCommand):
    help = 'Add 50 English texts to the database with various difficulties and word counts'

    def handle(self, *args, **options):
        # Sample English texts organized by word count
        texts_data = {
            10: [
                "The quick brown fox jumps over the lazy dog.",
                "Python is a powerful programming language for developers.",
                "Learning to code requires patience and consistent practice.",
                "Technology changes rapidly in the modern digital world.",
                "Practice makes perfect when learning new skills.",
                "Reading books expands your knowledge and vocabulary.",
                "Exercise daily to maintain good physical health.",
                "Friendship is one of life's greatest treasures.",
                "Music has the power to inspire and motivate people.",
                "Travel broadens your perspective on different cultures.",
                "Education opens doors to countless opportunities in life.",
                "Hard work and dedication lead to success eventually.",
                "Nature provides peace and tranquility for the mind.",
                "Cooking is both an art and a science skill.",
                "Time management is crucial for productivity at work.",
            ],
            25: [
                "The quick brown fox jumps over the lazy dog while running through the forest. This sentence contains every letter of the alphabet which makes it perfect for typing practice. Learning to type quickly and accurately is an essential skill in today's digital world.",
                "Python programming language is widely used for web development, data science, and artificial intelligence projects. Many developers prefer Python because of its simple syntax and powerful libraries. It's an excellent choice for beginners who want to start coding.",
                "Regular exercise and a balanced diet are essential components of a healthy lifestyle. Physical activity helps maintain cardiovascular health, strengthens muscles, and improves mental well-being. Making time for fitness should be a priority in everyone's daily routine.",
                "Reading books regularly can significantly improve your vocabulary, comprehension skills, and general knowledge. Whether you prefer fiction or non-fiction, books offer valuable insights into different perspectives and experiences from around the world.",
                "Effective communication skills are crucial for success in both personal and professional relationships. Learning to express your thoughts clearly and listen actively to others helps build stronger connections and resolve conflicts more efficiently.",
                "Time management is one of the most important skills for achieving productivity and reducing stress. By prioritizing tasks, setting realistic goals, and eliminating distractions, you can accomplish more in less time while maintaining work-life balance.",
                "Traveling to new places exposes you to different cultures, languages, and ways of life. These experiences broaden your perspective, challenge your assumptions, and create lasting memories that enrich your understanding of the world around you.",
                "Music has a profound impact on human emotions and can influence mood, motivation, and creativity. Whether you're listening to classical symphonies or modern pop songs, music provides entertainment and emotional expression for people worldwide.",
                "Learning a new language opens doors to new cultures, career opportunities, and personal growth. While it requires dedication and practice, the benefits of multilingualism include improved cognitive function and better communication with diverse communities.",
                "Technology continues to evolve at an unprecedented pace, transforming how we work, communicate, and live our daily lives. Staying updated with technological advancements helps individuals remain competitive in the modern job market.",
                "Innovation drives progress in every field from medicine to engineering. Creative thinking and problem-solving skills enable individuals to develop solutions that address complex challenges facing society today and in the future.",
                "Environmental conservation requires collective effort from individuals, communities, and governments worldwide. Simple actions like reducing waste, conserving energy, and supporting sustainable practices can make a significant positive impact on our planet.",
            ],
            60: [
                "The quick brown fox jumps over the lazy dog while running through the dense forest. This classic sentence contains every letter of the alphabet, making it perfect for typing practice sessions. Learning to type quickly and accurately has become an essential skill in today's digital world where most communication happens through keyboards. Regular practice helps improve your typing speed and reduces errors over time. Many professionals spend hours each day typing, so developing this skill can significantly boost your productivity at work. Typing trainers and practice websites offer various exercises to help beginners and advanced users improve their skills. The key to success is consistency and patience when learning any new ability.",
                "Python programming language has gained immense popularity among developers worldwide due to its simplicity and versatility. It's widely used in web development, data science, artificial intelligence, and automation projects. Many beginners choose Python as their first programming language because of its readable syntax and extensive documentation. The language offers powerful libraries and frameworks that make complex tasks easier to accomplish. Learning Python opens doors to numerous career opportunities in technology fields. Regular practice and building projects help developers master the language and understand its various applications. The programming community provides excellent support through forums, tutorials, and open-source contributions.",
                "Regular exercise and maintaining a balanced diet are fundamental components of a healthy lifestyle that everyone should prioritize. Physical activity helps strengthen your cardiovascular system, build muscle mass, and improve overall mental well-being. Many people struggle to find time for fitness in their busy schedules, but even short daily workouts can make a significant difference. A nutritious diet rich in fruits, vegetables, and whole grains provides essential vitamins and minerals your body needs. Combining exercise with proper nutrition creates a powerful foundation for long-term health and vitality. Making small, sustainable changes to your routine is more effective than drastic overhauls that are difficult to maintain.",
                "Reading books regularly provides numerous benefits beyond simple entertainment and knowledge acquisition. Literature exposes readers to different perspectives, cultures, and historical periods that expand their understanding of the world. Whether you prefer fiction novels that transport you to imaginary worlds or non-fiction books that teach practical skills, reading exercises your brain and improves cognitive function. Studies show that regular readers have better vocabulary, writing abilities, and analytical thinking skills. Books offer a unique form of entertainment that doesn't require screens or batteries, making them perfect companions for quiet moments. Building a reading habit takes time, but the intellectual and emotional rewards make the effort worthwhile.",
                "Effective communication skills are absolutely essential for success in both personal relationships and professional environments. Learning to express your thoughts clearly, listen actively to others, and understand non-verbal cues helps build stronger connections with people around you. Good communicators can resolve conflicts more efficiently, collaborate better in team settings, and inspire others through their words. The ability to convey complex ideas in simple terms is particularly valuable in leadership roles and educational contexts. Regular practice in various communication scenarios helps develop confidence and adaptability in different social situations. Investing time in improving these skills pays dividends throughout your entire life.",
            ],
            100: [
                "The quick brown fox jumps over the lazy dog while running through the dense forest on a beautiful sunny morning. This classic sentence contains every letter of the alphabet, making it perfect for typing practice sessions that help improve your keyboard skills. Learning to type quickly and accurately has become an essential skill in today's digital world where most communication and work happens through computers and mobile devices. Regular practice helps improve your typing speed, reduces errors over time, and builds muscle memory that makes typing feel natural and effortless. Many professionals spend several hours each day typing emails, documents, and code, so developing this skill can significantly boost your productivity at work. Typing trainers and practice websites offer various exercises designed to help both beginners and advanced users improve their skills through structured lessons and real-time feedback. The key to success in typing, as with any skill, is consistency, patience, and regular practice sessions that gradually increase in difficulty. Setting aside just fifteen minutes daily for typing practice can lead to noticeable improvements within a few weeks. Whether you're a student preparing for exams, a professional looking to work more efficiently, or someone simply wanting to communicate faster online, typing skills are valuable assets worth developing.",
                "Python programming language has gained immense popularity among developers worldwide due to its simplicity, versatility, and powerful capabilities that make it suitable for a wide range of applications. It's widely used in web development for creating dynamic websites and web applications, in data science for analyzing large datasets and building machine learning models, in artificial intelligence for developing intelligent systems, and in automation for streamlining repetitive tasks. Many beginners choose Python as their first programming language because of its readable syntax that closely resembles natural English, extensive documentation available online, and supportive community that provides help through forums and tutorials. The language offers powerful libraries and frameworks like Django for web development, NumPy and Pandas for data analysis, and TensorFlow for machine learning that make complex tasks easier to accomplish. Learning Python opens doors to numerous career opportunities in technology fields including software development, data analysis, cybersecurity, and artificial intelligence research. Regular practice through building projects, solving coding challenges, and contributing to open-source software helps developers master the language and understand its various applications in real-world scenarios. The programming community provides excellent support through online forums, video tutorials, coding bootcamps, and collaborative platforms where developers share knowledge and help each other grow.",
                "Regular exercise and maintaining a balanced diet are fundamental components of a healthy lifestyle that everyone should prioritize regardless of age, fitness level, or busy schedule. Physical activity helps strengthen your cardiovascular system by improving heart health and circulation, build muscle mass through resistance training, and improve overall mental well-being by releasing endorphins that reduce stress and anxiety. Many people struggle to find time for fitness in their busy schedules filled with work commitments, family responsibilities, and social activities, but even short daily workouts lasting just twenty to thirty minutes can make a significant difference in your health and energy levels. A nutritious diet rich in fruits, vegetables, whole grains, lean proteins, and healthy fats provides essential vitamins, minerals, and nutrients your body needs to function optimally and maintain strong immunity against diseases. Combining regular exercise with proper nutrition creates a powerful foundation for long-term health, vitality, and disease prevention that can improve your quality of life significantly. Making small, sustainable changes to your routine such as taking stairs instead of elevators, choosing water over sugary drinks, and adding one extra serving of vegetables to each meal is more effective than drastic overhauls that are difficult to maintain long-term.",
            ]
        }

        # Difficulty distribution
        difficulties = ['easy', 'hard']
        
        # Create texts
        created_count = 0
        total_needed = 50
        text_counter = 0  # Counter to ensure unique texts

        def generate_unique_text(word_count, difficulty, seed):
            """Generate a unique, word-count-accurate text using varied words to avoid duplicates."""
            rnd = random.Random(seed)
            topics = [
                "technology", "learning", "health", "travel", "productivity",
                "creativity", "communication", "leadership", "research", "community",
                "education", "science", "nature", "innovation", "design",
            ]
            verbs = [
                "builds", "inspires", "connects", "improves", "guides",
                "supports", "drives", "transforms", "shapes", "enables",
                "elevates", "refines", "develops", "encourages", "strengthens",
            ]
            adjectives = [
                "reliable", "practical", "innovative", "balanced", "focused",
                "collaborative", "thoughtful", "curious", "ambitious", "resilient",
                "efficient", "supportive", "creative", "patient", "consistent",
            ]
            nouns = [
                "skills", "ideas", "teams", "results", "habits",
                "projects", "solutions", "systems", "processes", "outcomes",
                "methods", "strategies", "insights", "goals", "challenges",
            ]
            closers = [
                "Keep practicing and refining your approach.",
                "Stay focused and measure progress frequently.",
                "Small daily actions compound into big gains.",
                "Consistency beats intensity over the long run.",
                "Curiosity and patience make learning sustainable.",
            ]

            words = []
            while len(words) < word_count - 8:  # leave room for a closing sentence
                topic = rnd.choice(topics)
                verb = rnd.choice(verbs)
                adj = rnd.choice(adjectives)
                noun = rnd.choice(nouns)
                fragment = f"{topic} {verb} {adj} {noun}"
                words.extend(fragment.split())

            # Add a short closing
            closing = rnd.choice(closers).split()
            words.extend(closing)

            # Trim or pad to exact word_count
            if len(words) > word_count:
                words = words[:word_count]
            elif len(words) < word_count:
                # pad with simple connector words to reach exact length
                fillers = ["and", "for", "with", "to", "in", "on", "by", "from"]
                while len(words) < word_count:
                    words.append(rnd.choice(fillers))

            # Capitalize first word and add period
            words[0] = words[0].capitalize()
            text_body = " ".join(words).rstrip(".") + "."
            return text_body
        
        # Distribute texts across word counts and difficulties
        word_counts = [10, 25, 60, 100]
        total_combinations = len(word_counts) * len(difficulties)
        texts_per_combination = total_needed // total_combinations
        remaining = total_needed % total_combinations
        
        # Additional texts to ensure we reach exactly 50
        additional_texts_needed = []
        for word_count in word_counts:
            for difficulty in difficulties:
                if remaining > 0:
                    additional_texts_needed.append((word_count, difficulty))
                    remaining -= 1
        
        for word_count in word_counts:
            for difficulty in difficulties:
                # Get texts for this word count
                available_texts = texts_data.get(word_count, [])
                if not available_texts:
                    continue
                
                # Calculate how many texts to create for this combination
                count = texts_per_combination
                if (word_count, difficulty) in additional_texts_needed:
                    count += 1
                
                # Create texts
                for i in range(count):
                    if i < len(available_texts):
                        text_body = available_texts[i]
                    else:
                        # Generate a unique text with exact word count to avoid duplicates
                        text_body = generate_unique_text(word_count, difficulty, seed=text_counter)
                    
                    # Create title (first few words + counter for uniqueness)
                    title_words = text_body.split()[:5]
                    title = ' '.join(title_words)
                    if len(title) > 50:
                        title = title[:47] + "..."
                    
                    # Add counter to make title unique
                    if text_counter > 0:
                        title = f"{title} ({text_counter})"
                    
                    # Create text object - always create new, don't check for duplicates
                    text = Text.objects.create(
                        title=title,
                        body=text_body,
                        difficulty=difficulty,
                        word_count=word_count
                    )
                    
                    created_count += 1
                    text_counter += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'Created: {title[:30]}... ({difficulty}, {word_count} words)')
                    )
                    
                    # Stop if we've created enough
                    if created_count >= total_needed:
                        break
                
                if created_count >= total_needed:
                    break
            
            if created_count >= total_needed:
                break
        
        self.stdout.write(
            self.style.SUCCESS(f'\nSuccessfully created {created_count} new text objects!')
        )

