from django.core.management.base import BaseCommand
from typing_practice.models import Text, CodeSnippet


class Command(BaseCommand):
    help = 'Seed database with sample texts and code snippets'

    def handle(self, *args, **options):
        # Easy Texts
        easy_texts = [
            ("The quick brown fox jumps over the lazy dog.", "A classic typing test sentence."),
            ("Python is a powerful programming language.", "Introduction to Python."),
            ("Practice makes perfect when learning to type.", "Motivational text."),
            ("The sun shines brightly in the clear blue sky.", "Nature description."),
            ("Learning to code opens many career opportunities.", "Career advice."),
            ("Reading books expands your knowledge and imagination.", "About reading."),
            ("Technology changes the way we live and work.", "Technology impact."),
            ("Friendship is one of life's greatest treasures.", "About friendship."),
            ("Exercise is important for maintaining good health.", "Health advice."),
            ("Music has the power to inspire and motivate.", "About music."),
            ("Traveling allows you to experience new cultures.", "About travel."),
            ("Cooking can be both creative and relaxing.", "About cooking."),
            ("Education is the key to personal growth.", "About education."),
            ("Nature provides peace and tranquility.", "Nature benefits."),
            ("Hard work and dedication lead to success.", "Success advice."),
            ("Art expresses emotions and tells stories.", "About art."),
            ("Science helps us understand the world.", "About science."),
            ("Family provides love and support.", "About family."),
            ("Dreams give us goals to strive for.", "About dreams."),
            ("Kindness makes the world a better place.", "About kindness."),
            ("History teaches us valuable lessons.", "About history."),
            ("Innovation drives progress in society.", "About innovation."),
            ("Teamwork achieves greater results.", "About teamwork."),
            ("Patience is a valuable virtue.", "About patience."),
            ("Curiosity leads to discovery and learning.", "About curiosity."),
            ("Gratitude improves happiness and well-being.", "About gratitude."),
            ("Communication builds strong relationships.", "About communication."),
            ("Time management increases productivity.", "About time management."),
            ("Creativity solves complex problems.", "About creativity."),
            ("Resilience helps overcome challenges.", "About resilience."),
            ("Honesty builds trust and respect.", "About honesty."),
            ("Learning never stops throughout life.", "Lifelong learning."),
            ("Adventure awaits those who seek it.", "About adventure."),
            ("Wisdom comes from experience and reflection.", "About wisdom."),
            ("Hope provides strength during difficult times.", "About hope."),
            ("Balance is key to a fulfilling life.", "About balance."),
            ("Passion drives excellence in any field.", "About passion."),
            ("Empathy connects us with others.", "About empathy."),
            ("Perseverance overcomes obstacles.", "About perseverance."),
            ("Optimism creates positive outcomes.", "About optimism."),
            ("Discipline builds character and achievement.", "About discipline."),
            ("Compassion makes us more human.", "About compassion."),
            ("Integrity guides ethical decisions.", "About integrity."),
            ("Courage enables us to face fears.", "About courage."),
            ("Humility keeps us grounded.", "About humility."),
            ("Generosity enriches both giver and receiver.", "About generosity."),
            ("Focus improves performance and results.", "About focus."),
            ("Adaptability ensures survival and success.", "About adaptability."),
            ("Excellence is a habit, not an act.", "About excellence."),
        ]

        # Hard Texts
        hard_texts = [
            ("The intricate mechanisms of quantum computing revolutionize data processing, enabling unprecedented computational capabilities through superposition and entanglement principles.", "Complex technology topic."),
            ("Philosophical discourse on existentialism explores the fundamental questions of human existence, freedom, and the search for meaning in an apparently meaningless universe.", "Philosophy text."),
            ("Meteorological phenomena, including atmospheric pressure variations, temperature gradients, and humidity levels, significantly influence weather patterns across different geographical regions.", "Meteorology text."),
            ("Neuroscientific research reveals the complex neural pathways and synaptic connections that govern cognitive functions, memory formation, and behavioral responses in the human brain.", "Neuroscience text."),
            ("Economic theories analyze market dynamics, supply and demand relationships, inflation rates, and fiscal policies that shape global financial systems and trade relationships.", "Economics text."),
            ("Linguistic analysis examines phonetics, syntax, semantics, and pragmatics to understand how languages evolve, communicate meaning, and reflect cultural identities.", "Linguistics text."),
            ("Astrophysical observations utilize advanced telescopes and spectroscopy to study celestial bodies, stellar evolution, black holes, and the expansion of the universe.", "Astrophysics text."),
            ("Biochemical processes involve enzyme catalysis, metabolic pathways, and molecular interactions that sustain life at the cellular and organismal levels.", "Biochemistry text."),
            ("Archaeological discoveries provide insights into ancient civilizations, their social structures, technological achievements, and cultural practices through material remains.", "Archaeology text."),
            ("Psychological research investigates cognitive processes, emotional regulation, personality development, and behavioral patterns that influence human thought and action.", "Psychology text."),
            ("Mathematical theorems and proofs establish logical foundations for abstract concepts, geometric relationships, and numerical systems that describe natural phenomena.", "Mathematics text."),
            ("Literary analysis explores narrative techniques, thematic elements, character development, and stylistic devices that convey meaning and evoke emotional responses.", "Literature text."),
            ("Environmental science addresses ecosystem dynamics, biodiversity conservation, climate change impacts, and sustainable resource management strategies.", "Environmental science text."),
            ("Medical research advances understanding of disease mechanisms, treatment protocols, pharmaceutical interventions, and preventive healthcare measures.", "Medical research text."),
            ("Sociological studies examine social structures, cultural norms, institutional frameworks, and collective behaviors that shape human interactions.", "Sociology text."),
            ("Engineering principles apply scientific knowledge to design solutions, optimize systems, and create innovative technologies that address practical challenges.", "Engineering text."),
            ("Historical analysis interprets past events, political movements, economic transformations, and cultural shifts that have shaped contemporary societies.", "History text."),
            ("Anthropological research investigates human evolution, cultural diversity, social organization, and adaptive strategies across different populations and time periods.", "Anthropology text."),
            ("Geological processes, including tectonic movements, erosion patterns, and mineral formation, continuously reshape the Earth's surface and subsurface structures.", "Geology text."),
            ("Political science examines governance systems, policy formulation, electoral processes, and international relations that influence global and domestic affairs.", "Political science text."),
            ("Chemical reactions involve molecular transformations, bond formations, energy exchanges, and equilibrium states that drive natural and synthetic processes.", "Chemistry text."),
            ("Artistic expression encompasses diverse media, creative techniques, aesthetic principles, and cultural contexts that communicate ideas and emotions.", "Art text."),
            ("Musical composition integrates harmony, rhythm, melody, and timbre to create expressive works that reflect cultural traditions and individual creativity.", "Music text."),
            ("Architectural design balances aesthetic considerations, structural integrity, functional requirements, and environmental sustainability in built environments.", "Architecture text."),
            ("Theological discourse explores religious beliefs, spiritual practices, moral frameworks, and questions of faith that shape human understanding of the divine.", "Theology text."),
            ("Computer science develops algorithms, data structures, software systems, and computational models that enable digital technologies and information processing.", "Computer science text."),
            ("Legal frameworks establish rights, obligations, procedures, and remedies that govern individual conduct and institutional operations within societies.", "Law text."),
            ("Educational methodologies employ pedagogical strategies, learning theories, assessment techniques, and curriculum design to facilitate knowledge acquisition.", "Education text."),
            ("Agricultural practices integrate crop cultivation, livestock management, soil conservation, and sustainable farming techniques to ensure food security.", "Agriculture text."),
            ("Marine biology studies ocean ecosystems, aquatic organisms, biodiversity patterns, and environmental factors that influence marine life and habitats.", "Marine biology text."),
            ("Urban planning addresses infrastructure development, transportation systems, housing policies, and sustainable city design to improve quality of life.", "Urban planning text."),
            ("Forensic science applies scientific methods to investigate crimes, analyze evidence, identify suspects, and support legal proceedings through objective analysis.", "Forensic science text."),
            ("Veterinary medicine provides healthcare services for animals, diagnoses diseases, performs surgeries, and promotes animal welfare and public health.", "Veterinary medicine text."),
            ("Journalism reports news events, investigates stories, analyzes information, and communicates developments to inform public discourse and democratic participation.", "Journalism text."),
            ("Philosophy of science examines the nature of scientific knowledge, methodological approaches, theoretical frameworks, and the relationship between science and reality.", "Philosophy of science text."),
            ("Biotechnology applies biological systems and organisms to develop products, improve processes, and solve problems in medicine, agriculture, and industry.", "Biotechnology text."),
            ("Renewable energy technologies harness solar, wind, hydroelectric, and geothermal resources to generate sustainable power and reduce environmental impacts.", "Renewable energy text."),
            ("Data science combines statistical analysis, machine learning, and computational tools to extract insights, identify patterns, and support decision-making processes.", "Data science text."),
            ("Robotics integrates mechanical engineering, electronics, and computer programming to create autonomous systems that perform tasks in various environments.", "Robotics text."),
            ("Nanotechnology manipulates matter at atomic and molecular scales to create materials, devices, and systems with novel properties and applications.", "Nanotechnology text."),
            ("Cryptography secures information through encryption algorithms, key management, and authentication protocols that protect data confidentiality and integrity.", "Cryptography text."),
            ("Genomics studies complete sets of genetic material, analyzes DNA sequences, identifies gene functions, and explores relationships between genes and traits.", "Genomics text."),
            ("Virtual reality creates immersive digital environments using computer-generated simulations, sensory feedback, and interactive technologies for various applications.", "Virtual reality text."),
            ("Space exploration advances scientific knowledge, develops technologies, and expands human presence beyond Earth through missions, research, and international collaboration.", "Space exploration text."),
            ("Artificial intelligence develops systems that perceive, learn, reason, and make decisions, transforming industries and creating new possibilities.", "Artificial intelligence text."),
            ("Sustainable development balances economic growth, environmental protection, and social equity to meet present needs without compromising future generations.", "Sustainable development text."),
            ("Bioinformatics combines biology, computer science, and mathematics to analyze biological data, model biological systems, and advance medical research.", "Bioinformatics text."),
            ("Materials science investigates the properties, structures, and applications of substances to develop new materials with enhanced performance characteristics.", "Materials science text."),
        ]

        # Python Code Snippets
        python_codes = [
            ("Hello World", "python", "easy", "print('Hello, World!')"),
            ("Variables", "python", "easy", "name = 'John'\nage = 25\nprint(f'My name is {name} and I am {age} years old')"),
            ("List Operations", "python", "easy", "numbers = [1, 2, 3, 4, 5]\nsum_numbers = sum(numbers)\nprint(f'Sum: {sum_numbers}')"),
            ("Function Definition", "python", "easy", "def greet(name):\n    return f'Hello, {name}!'\n\nmessage = greet('Alice')\nprint(message)"),
            ("Loop Example", "python", "easy", "for i in range(5):\n    print(f'Number: {i}')"),
            ("Conditional Statement", "python", "easy", "x = 10\nif x > 5:\n    print('x is greater than 5')\nelse:\n    print('x is not greater than 5')"),
            ("Dictionary", "python", "easy", "student = {\n    'name': 'Bob',\n    'age': 20,\n    'grade': 'A'\n}\nprint(student['name'])"),
            ("List Comprehension", "python", "medium", "squares = [x**2 for x in range(10)]\nprint(squares)"),
            ("Class Definition", "python", "medium", "class Person:\n    def __init__(self, name, age):\n        self.name = name\n        self.age = age\n    \n    def introduce(self):\n        return f'I am {self.name}, {self.age} years old'\n\nperson = Person('Alice', 30)\nprint(person.introduce())"),
            ("Exception Handling", "python", "medium", "try:\n    result = 10 / 0\nexcept ZeroDivisionError:\n    print('Cannot divide by zero')\nfinally:\n    print('Operation completed')"),
            ("File Operations", "python", "medium", "with open('data.txt', 'w') as f:\n    f.write('Hello, File!')\n\nwith open('data.txt', 'r') as f:\n    content = f.read()\n    print(content)"),
            ("Lambda Function", "python", "medium", "numbers = [1, 2, 3, 4, 5]\nsquared = list(map(lambda x: x**2, numbers))\nprint(squared)"),
            ("Generator Function", "python", "hard", "def fibonacci(n):\n    a, b = 0, 1\n    for _ in range(n):\n        yield a\n        a, b = b, a + b\n\nfor num in fibonacci(10):\n    print(num)"),
            ("Decorator Pattern", "python", "hard", "def timer_decorator(func):\n    def wrapper(*args, **kwargs):\n        import time\n        start = time.time()\n        result = func(*args, **kwargs)\n        end = time.time()\n        print(f'Execution time: {end - start} seconds')\n        return result\n    return wrapper\n\n@timer_decorator\ndef slow_function():\n    time.sleep(1)\n    return 'Done'\n\nslow_function()"),
            ("Context Manager", "python", "hard", "class FileManager:\n    def __init__(self, filename, mode):\n        self.filename = filename\n        self.mode = mode\n    \n    def __enter__(self):\n        self.file = open(self.filename, self.mode)\n        return self.file\n    \n    def __exit__(self, exc_type, exc_val, exc_tb):\n        self.file.close()\n\nwith FileManager('test.txt', 'w') as f:\n    f.write('Test content')"),
            ("Async Function", "python", "hard", "import asyncio\n\nasync def fetch_data():\n    await asyncio.sleep(1)\n    return 'Data fetched'\n\nasync def main():\n    result = await fetch_data()\n    print(result)\n\nasyncio.run(main())"),
            ("Regular Expression", "python", "hard", "import re\n\ntext = 'Contact: email@example.com or phone: 123-456-7890'\nemail_pattern = r'\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b'\nemails = re.findall(email_pattern, text)\nprint(emails)"),
            ("Data Class", "python", "medium", "from dataclasses import dataclass\n\n@dataclass\nclass Point:\n    x: int\n    y: int\n    \n    def distance(self, other):\n        return ((self.x - other.x)**2 + (self.y - other.y)**2)**0.5\n\np1 = Point(0, 0)\np2 = Point(3, 4)\nprint(p1.distance(p2))"),
            ("List Sorting", "python", "easy", "students = [\n    {'name': 'Alice', 'score': 85},\n    {'name': 'Bob', 'score': 92},\n    {'name': 'Charlie', 'score': 78}\n]\nsorted_students = sorted(students, key=lambda x: x['score'], reverse=True)\nfor student in sorted_students:\n    print(f\"{student['name']}: {student['score']}\")"),
            ("String Methods", "python", "easy", "text = '  Hello, World!  '\ncleaned = text.strip().lower().replace('world', 'Python')\nprint(cleaned)"),
        ]

        # JavaScript Code Snippets
        javascript_codes = [
            ("Hello World", "javascript", "easy", "console.log('Hello, World!');"),
            ("Variables", "javascript", "easy", "const name = 'John';\nconst age = 25;\nconsole.log(`My name is ${name} and I am ${age} years old`);"),
            ("Array Operations", "javascript", "easy", "const numbers = [1, 2, 3, 4, 5];\nconst sum = numbers.reduce((a, b) => a + b, 0);\nconsole.log(`Sum: ${sum}`);"),
            ("Function Definition", "javascript", "easy", "function greet(name) {\n    return `Hello, ${name}!`;\n}\n\nconst message = greet('Alice');\nconsole.log(message);"),
            ("Arrow Function", "javascript", "easy", "const multiply = (a, b) => a * b;\nconst result = multiply(5, 3);\nconsole.log(result);"),
            ("Object Literal", "javascript", "easy", "const student = {\n    name: 'Bob',\n    age: 20,\n    grade: 'A'\n};\nconsole.log(student.name);"),
            ("Array Methods", "javascript", "medium", "const numbers = [1, 2, 3, 4, 5];\nconst doubled = numbers.map(n => n * 2);\nconst evens = doubled.filter(n => n % 2 === 0);\nconsole.log(evens);"),
            ("Class Definition", "javascript", "medium", "class Person {\n    constructor(name, age) {\n        this.name = name;\n        this.age = age;\n    }\n    \n    introduce() {\n        return `I am ${this.name}, ${this.age} years old`;\n    }\n}\n\nconst person = new Person('Alice', 30);\nconsole.log(person.introduce());"),
            ("Promise", "javascript", "medium", "const fetchData = () => {\n    return new Promise((resolve) => {\n        setTimeout(() => {\n            resolve('Data fetched');\n        }, 1000);\n    });\n};\n\nfetchData().then(data => console.log(data));"),
            ("Async/Await", "javascript", "hard", "async function fetchUserData() {\n    try {\n        const response = await fetch('/api/user');\n        const data = await response.json();\n        return data;\n    } catch (error) {\n        console.error('Error:', error);\n    }\n}\n\nfetchUserData();"),
            ("Destructuring", "javascript", "medium", "const person = { name: 'John', age: 30, city: 'NYC' };\nconst { name, age } = person;\nconsole.log(`${name} is ${age} years old`);"),
            ("Spread Operator", "javascript", "medium", "const arr1 = [1, 2, 3];\nconst arr2 = [4, 5, 6];\nconst combined = [...arr1, ...arr2];\nconsole.log(combined);"),
            ("Closure", "javascript", "hard", "function createCounter() {\n    let count = 0;\n    return function() {\n        count++;\n        return count;\n    };\n}\n\nconst counter = createCounter();\nconsole.log(counter());\nconsole.log(counter());"),
            ("Event Handler", "javascript", "medium", "document.addEventListener('DOMContentLoaded', () => {\n    const button = document.getElementById('myButton');\n    button.addEventListener('click', () => {\n        console.log('Button clicked!');\n    });\n});"),
            ("JSON Operations", "javascript", "easy", "const data = { name: 'John', age: 30 };\nconst jsonString = JSON.stringify(data);\nconst parsed = JSON.parse(jsonString);\nconsole.log(parsed.name);"),
            ("Array Filter", "javascript", "easy", "const numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];\nconst evens = numbers.filter(n => n % 2 === 0);\nconsole.log(evens);"),
            ("Template Literals", "javascript", "easy", "const name = 'Alice';\nconst age = 25;\nconst message = `Hello, my name is ${name} and I am ${age} years old.`;\nconsole.log(message);"),
            ("Set and Map", "javascript", "medium", "const uniqueNumbers = new Set([1, 2, 2, 3, 3, 4]);\nconst userMap = new Map([\n    ['name', 'John'],\n    ['age', 30]\n]);\nconsole.log(uniqueNumbers.size);\nconsole.log(userMap.get('name'));"),
            ("Generator Function", "javascript", "hard", "function* fibonacci() {\n    let [a, b] = [0, 1];\n    while (true) {\n        yield a;\n        [a, b] = [b, a + b];\n    }\n}\n\nconst fib = fibonacci();\nfor (let i = 0; i < 10; i++) {\n    console.log(fib.next().value);\n}"),
            ("Proxy", "javascript", "hard", "const handler = {\n    get: (target, prop) => {\n        return prop in target ? target[prop] : 'Not found';\n    }\n};\n\nconst proxy = new Proxy({ name: 'John' }, handler);\nconsole.log(proxy.name);\nconsole.log(proxy.age);"),
        ]

        # C++ Code Snippets
        cpp_codes = [
            ("Hello World", "cpp", "easy", "#include <iostream>\nusing namespace std;\n\nint main() {\n    cout << \"Hello, World!\" << endl;\n    return 0;\n}"),
            ("Variables", "cpp", "easy", "#include <iostream>\nusing namespace std;\n\nint main() {\n    string name = \"John\";\n    int age = 25;\n    cout << \"Name: \" << name << \", Age: \" << age << endl;\n    return 0;\n}"),
            ("Array", "cpp", "easy", "#include <iostream>\nusing namespace std;\n\nint main() {\n    int numbers[5] = {1, 2, 3, 4, 5};\n    int sum = 0;\n    for (int i = 0; i < 5; i++) {\n        sum += numbers[i];\n    }\n    cout << \"Sum: \" << sum << endl;\n    return 0;\n}"),
            ("Function", "cpp", "easy", "#include <iostream>\nusing namespace std;\n\nint add(int a, int b) {\n    return a + b;\n}\n\nint main() {\n    int result = add(5, 3);\n    cout << \"Result: \" << result << endl;\n    return 0;\n}"),
            ("Loop", "cpp", "easy", "#include <iostream>\nusing namespace std;\n\nint main() {\n    for (int i = 0; i < 5; i++) {\n        cout << \"Number: \" << i << endl;\n    }\n    return 0;\n}"),
            ("Conditional", "cpp", "easy", "#include <iostream>\nusing namespace std;\n\nint main() {\n    int x = 10;\n    if (x > 5) {\n        cout << \"x is greater than 5\" << endl;\n    } else {\n        cout << \"x is not greater than 5\" << endl;\n    }\n    return 0;\n}"),
            ("Vector", "cpp", "medium", "#include <iostream>\n#include <vector>\nusing namespace std;\n\nint main() {\n    vector<int> numbers = {1, 2, 3, 4, 5};\n    numbers.push_back(6);\n    for (int num : numbers) {\n        cout << num << \" \";\n    }\n    return 0;\n}"),
            ("Class", "cpp", "medium", "#include <iostream>\n#include <string>\nusing namespace std;\n\nclass Person {\nprivate:\n    string name;\n    int age;\npublic:\n    Person(string n, int a) : name(n), age(a) {}\n    void introduce() {\n        cout << \"I am \" << name << \", \" << age << \" years old\" << endl;\n    }\n};\n\nint main() {\n    Person person(\"Alice\", 30);\n    person.introduce();\n    return 0;\n}"),
            ("Pointer", "cpp", "medium", "#include <iostream>\nusing namespace std;\n\nint main() {\n    int x = 10;\n    int* ptr = &x;\n    cout << \"Value: \" << *ptr << endl;\n    cout << \"Address: \" << ptr << endl;\n    return 0;\n}"),
            ("String Operations", "cpp", "easy", "#include <iostream>\n#include <string>\nusing namespace std;\n\nint main() {\n    string text = \"Hello, World!\";\n    cout << \"Length: \" << text.length() << endl;\n    cout << \"Substring: \" << text.substr(0, 5) << endl;\n    return 0;\n}"),
            ("STL Algorithm", "cpp", "hard", "#include <iostream>\n#include <algorithm>\n#include <vector>\nusing namespace std;\n\nint main() {\n    vector<int> numbers = {5, 2, 8, 1, 9};\n    sort(numbers.begin(), numbers.end());\n    for (int num : numbers) {\n        cout << num << \" \";\n    }\n    return 0;\n}"),
            ("Template Function", "cpp", "hard", "#include <iostream>\nusing namespace std;\n\ntemplate <typename T>\nT maximum(T a, T b) {\n    return (a > b) ? a : b;\n}\n\nint main() {\n    cout << maximum(5, 10) << endl;\n    cout << maximum(3.5, 2.1) << endl;\n    return 0;\n}"),
            ("Exception Handling", "cpp", "medium", "#include <iostream>\nusing namespace std;\n\nint main() {\n    try {\n        int x = 10, y = 0;\n        if (y == 0) throw \"Division by zero\";\n        int result = x / y;\n    } catch (const char* msg) {\n        cout << \"Error: \" << msg << endl;\n    }\n    return 0;\n}"),
            ("File I/O", "cpp", "medium", "#include <iostream>\n#include <fstream>\nusing namespace std;\n\nint main() {\n    ofstream file(\"data.txt\");\n    file << \"Hello, File!\" << endl;\n    file.close();\n    \n    ifstream readFile(\"data.txt\");\n    string line;\n    getline(readFile, line);\n    cout << line << endl;\n    return 0;\n}"),
            ("Lambda Expression", "cpp", "hard", "#include <iostream>\n#include <vector>\n#include <algorithm>\nusing namespace std;\n\nint main() {\n    vector<int> numbers = {1, 2, 3, 4, 5};\n    for_each(numbers.begin(), numbers.end(), [](int n) {\n        cout << n * 2 << \" \";\n    });\n    return 0;\n}"),
            ("Smart Pointer", "cpp", "hard", "#include <iostream>\n#include <memory>\nusing namespace std;\n\nint main() {\n    unique_ptr<int> ptr(new int(42));\n    cout << *ptr << endl;\n    return 0;\n}"),
            ("STL Map", "cpp", "medium", "#include <iostream>\n#include <map>\nusing namespace std;\n\nint main() {\n    map<string, int> scores;\n    scores[\"Alice\"] = 95;\n    scores[\"Bob\"] = 87;\n    for (auto& pair : scores) {\n        cout << pair.first << \": \" << pair.second << endl;\n    }\n    return 0;\n}"),
            ("Recursion", "cpp", "medium", "#include <iostream>\nusing namespace std;\n\nint factorial(int n) {\n    if (n <= 1) return 1;\n    return n * factorial(n - 1);\n}\n\nint main() {\n    cout << \"Factorial of 5: \" << factorial(5) << endl;\n    return 0;\n}"),
            ("Operator Overloading", "cpp", "hard", "#include <iostream>\nusing namespace std;\n\nclass Vector {\npublic:\n    int x, y;\n    Vector(int x, int y) : x(x), y(y) {}\n    Vector operator+(const Vector& other) {\n        return Vector(x + other.x, y + other.y);\n    }\n};\n\nint main() {\n    Vector v1(1, 2), v2(3, 4);\n    Vector v3 = v1 + v2;\n    cout << v3.x << \", \" << v3.y << endl;\n    return 0;\n}"),
            ("Namespace", "cpp", "easy", "#include <iostream>\n\nnamespace Math {\n    int add(int a, int b) {\n        return a + b;\n    }\n}\n\nint main() {\n    std::cout << Math::add(5, 3) << std::endl;\n    return 0;\n}"),
        ]

        # Java Code Snippets
        java_codes = [
            ("Hello World", "java", "easy", "public class HelloWorld {\n    public static void main(String[] args) {\n        System.out.println(\"Hello, World!\");\n    }\n}"),
            ("Variables", "java", "easy", "public class Variables {\n    public static void main(String[] args) {\n        String name = \"John\";\n        int age = 25;\n        System.out.println(\"Name: \" + name + \", Age: \" + age);\n    }\n}"),
            ("Array", "java", "easy", "public class ArrayExample {\n    public static void main(String[] args) {\n        int[] numbers = {1, 2, 3, 4, 5};\n        int sum = 0;\n        for (int num : numbers) {\n            sum += num;\n        }\n        System.out.println(\"Sum: \" + sum);\n    }\n}"),
            ("Method", "java", "easy", "public class MethodExample {\n    public static int add(int a, int b) {\n        return a + b;\n    }\n    \n    public static void main(String[] args) {\n        int result = add(5, 3);\n        System.out.println(\"Result: \" + result);\n    }\n}"),
            ("Loop", "java", "easy", "public class LoopExample {\n    public static void main(String[] args) {\n        for (int i = 0; i < 5; i++) {\n            System.out.println(\"Number: \" + i);\n        }\n    }\n}"),
            ("Conditional", "java", "easy", "public class ConditionalExample {\n    public static void main(String[] args) {\n        int x = 10;\n        if (x > 5) {\n            System.out.println(\"x is greater than 5\");\n        } else {\n            System.out.println(\"x is not greater than 5\");\n        }\n    }\n}"),
            ("ArrayList", "java", "medium", "import java.util.ArrayList;\n\npublic class ArrayListExample {\n    public static void main(String[] args) {\n        ArrayList<String> names = new ArrayList<>();\n        names.add(\"Alice\");\n        names.add(\"Bob\");\n        for (String name : names) {\n            System.out.println(name);\n        }\n    }\n}"),
            ("Class", "java", "medium", "public class Person {\n    private String name;\n    private int age;\n    \n    public Person(String name, int age) {\n        this.name = name;\n        this.age = age;\n    }\n    \n    public void introduce() {\n        System.out.println(\"I am \" + name + \", \" + age + \" years old\");\n    }\n    \n    public static void main(String[] args) {\n        Person person = new Person(\"Alice\", 30);\n        person.introduce();\n    }\n}"),
            ("Inheritance", "java", "medium", "class Animal {\n    void makeSound() {\n        System.out.println(\"Some sound\");\n    }\n}\n\nclass Dog extends Animal {\n    @Override\n    void makeSound() {\n        System.out.println(\"Woof!\");\n    }\n}\n\npublic class InheritanceExample {\n    public static void main(String[] args) {\n        Dog dog = new Dog();\n        dog.makeSound();\n    }\n}"),
            ("Exception Handling", "java", "medium", "public class ExceptionExample {\n    public static void main(String[] args) {\n        try {\n            int result = 10 / 0;\n        } catch (ArithmeticException e) {\n            System.out.println(\"Error: \" + e.getMessage());\n        } finally {\n            System.out.println(\"Operation completed\");\n        }\n    }\n}"),
            ("String Methods", "java", "easy", "public class StringExample {\n    public static void main(String[] args) {\n        String text = \"  Hello, World!  \";\n        String cleaned = text.trim().toLowerCase().replace(\"world\", \"Java\");\n        System.out.println(cleaned);\n    }\n}"),
            ("HashMap", "java", "medium", "import java.util.HashMap;\n\npublic class HashMapExample {\n    public static void main(String[] args) {\n        HashMap<String, Integer> scores = new HashMap<>();\n        scores.put(\"Alice\", 95);\n        scores.put(\"Bob\", 87);\n        System.out.println(scores.get(\"Alice\"));\n    }\n}"),
            ("Interface", "java", "hard", "interface Drawable {\n    void draw();\n}\n\nclass Circle implements Drawable {\n    @Override\n    public void draw() {\n        System.out.println(\"Drawing a circle\");\n    }\n}\n\npublic class InterfaceExample {\n    public static void main(String[] args) {\n        Drawable shape = new Circle();\n        shape.draw();\n    }\n}"),
            ("Generic Class", "java", "hard", "class Box<T> {\n    private T item;\n    \n    public void setItem(T item) {\n        this.item = item;\n    }\n    \n    public T getItem() {\n        return item;\n    }\n}\n\npublic class GenericExample {\n    public static void main(String[] args) {\n        Box<String> stringBox = new Box<>();\n        stringBox.setItem(\"Hello\");\n        System.out.println(stringBox.getItem());\n    }\n}"),
            ("Lambda Expression", "java", "hard", "import java.util.Arrays;\nimport java.util.List;\n\npublic class LambdaExample {\n    public static void main(String[] args) {\n        List<Integer> numbers = Arrays.asList(1, 2, 3, 4, 5);\n        numbers.forEach(n -> System.out.println(n * 2));\n    }\n}"),
            ("File I/O", "java", "medium", "import java.io.*;\n\npublic class FileExample {\n    public static void main(String[] args) {\n        try {\n            FileWriter writer = new FileWriter(\"data.txt\");\n            writer.write(\"Hello, File!\");\n            writer.close();\n            \n            FileReader reader = new FileReader(\"data.txt\");\n            int ch;\n            while ((ch = reader.read()) != -1) {\n                System.out.print((char) ch);\n            }\n            reader.close();\n        } catch (IOException e) {\n            e.printStackTrace();\n        }\n    }\n}"),
            ("Thread", "java", "hard", "class MyThread extends Thread {\n    public void run() {\n        System.out.println(\"Thread is running\");\n    }\n}\n\npublic class ThreadExample {\n    public static void main(String[] args) {\n        MyThread thread = new MyThread();\n        thread.start();\n    }\n}"),
            ("Stream API", "java", "hard", "import java.util.Arrays;\nimport java.util.List;\n\npublic class StreamExample {\n    public static void main(String[] args) {\n        List<Integer> numbers = Arrays.asList(1, 2, 3, 4, 5);\n        int sum = numbers.stream()\n                        .filter(n -> n % 2 == 0)\n                        .mapToInt(n -> n)\n                        .sum();\n        System.out.println(\"Sum of evens: \" + sum);\n    }\n}"),
            ("Enum", "java", "medium", "enum Day {\n    MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY\n}\n\npublic class EnumExample {\n    public static void main(String[] args) {\n        Day today = Day.MONDAY;\n        System.out.println(\"Today is: \" + today);\n    }\n}"),
            ("Recursion", "java", "medium", "public class RecursionExample {\n    public static int factorial(int n) {\n        if (n <= 1) return 1;\n        return n * factorial(n - 1);\n    }\n    \n    public static void main(String[] args) {\n        System.out.println(\"Factorial of 5: \" + factorial(5));\n    }\n}"),
        ]

        # Create texts
        self.stdout.write('Creating easy texts...')
        for title, body in easy_texts:
            Text.objects.get_or_create(
                title=title,
                defaults={'difficulty': 'easy', 'body': body}
            )
        self.stdout.write(self.style.SUCCESS(f'Created {len(easy_texts)} easy texts'))

        self.stdout.write('Creating hard texts...')
        for title, body in hard_texts:
            Text.objects.get_or_create(
                title=title,
                defaults={'difficulty': 'hard', 'body': body}
            )
        self.stdout.write(self.style.SUCCESS(f'Created {len(hard_texts)} hard texts'))

        # Create code snippets
        self.stdout.write('Creating Python code snippets...')
        for title, lang, diff, code in python_codes:
            CodeSnippet.objects.get_or_create(
                title=title,
                defaults={'language': lang, 'difficulty': diff, 'code_body': code}
            )
        self.stdout.write(self.style.SUCCESS(f'Created {len(python_codes)} Python snippets'))

        self.stdout.write('Creating JavaScript code snippets...')
        for title, lang, diff, code in javascript_codes:
            CodeSnippet.objects.get_or_create(
                title=title,
                defaults={'language': lang, 'difficulty': diff, 'code_body': code}
            )
        self.stdout.write(self.style.SUCCESS(f'Created {len(javascript_codes)} JavaScript snippets'))

        self.stdout.write('Creating C++ code snippets...')
        for title, lang, diff, code in cpp_codes:
            CodeSnippet.objects.get_or_create(
                title=title,
                defaults={'language': lang, 'difficulty': diff, 'code_body': code}
            )
        self.stdout.write(self.style.SUCCESS(f'Created {len(cpp_codes)} C++ snippets'))

        self.stdout.write('Creating Java code snippets...')
        for title, lang, diff, code in java_codes:
            CodeSnippet.objects.get_or_create(
                title=title,
                defaults={'language': lang, 'difficulty': diff, 'code_body': code}
            )
        self.stdout.write(self.style.SUCCESS(f'Created {len(java_codes)} Java snippets'))

        self.stdout.write(self.style.SUCCESS('Database seeding completed!'))

