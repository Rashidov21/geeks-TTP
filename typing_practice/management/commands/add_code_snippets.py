from django.core.management.base import BaseCommand
from typing_practice.models import CodeSnippet


class Command(BaseCommand):
    help = "Add additional code snippets for each language/difficulty"

    def handle(self, *args, **options):
        snippets = [
            # Python
            {
                "title": "Python | FizzBuzz easy",
                "language": "python",
                "difficulty": "easy",
                "code_body": """def fizzbuzz(n):
    for i in range(1, n + 1):
        if i % 15 == 0:
            print("FizzBuzz")
        elif i % 3 == 0:
            print("Fizz")
        elif i % 5 == 0:
            print("Buzz")
        else:
            print(i)

fizzbuzz(20)
""",
            },
            {
                "title": "Python | List comprehension medium",
                "language": "python",
                "difficulty": "medium",
                "code_body": """names = ["alice", "Bob", "charlie", "dave"]
normalized = [name.strip().title() for name in names if name]
print(", ".join(normalized))
""",
            },
            {
                "title": "Python | Memoized fibonacci hard",
                "language": "python",
                "difficulty": "hard",
                "code_body": """from functools import lru_cache

@lru_cache(maxsize=None)
def fib(n):
    if n < 2:
        return n
    return fib(n-1) + fib(n-2)

print([fib(i) for i in range(15)])
""",
            },
            # JavaScript
            {
                "title": "JavaScript | Debounce utility easy",
                "language": "javascript",
                "difficulty": "easy",
                "code_body": """function debounce(fn, delay) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}

const log = debounce(() => console.log("Hello"), 300);
log();
""",
            },
            {
                "title": "JavaScript | Fetch JSON medium",
                "language": "javascript",
                "difficulty": "medium",
                "code_body": """async function loadUsers() {
  const res = await fetch("https://jsonplaceholder.typicode.com/users");
  if (!res.ok) throw new Error("Request failed");
  const data = await res.json();
  return data.map(u => u.name);
}

loadUsers().then(console.log).catch(console.error);
""",
            },
            {
                "title": "JavaScript | Promise all hard",
                "language": "javascript",
                "difficulty": "hard",
                "code_body": """const endpoints = ["/a", "/b", "/c"];

async function fetchAll() {
  const responses = await Promise.all(endpoints.map(url => fetch(url)));
  return Promise.all(responses.map(r => r.json()));
}

fetchAll().then(console.log).catch(console.error);
""",
            },
            # C++
            {
                "title": "C++ | Vector sum easy",
                "language": "cpp",
                "difficulty": "easy",
                "code_body": """#include <bits/stdc++.h>
using namespace std;

int main() {
    vector<int> v = {1, 2, 3, 4, 5};
    int sum = accumulate(v.begin(), v.end(), 0);
    cout << sum << endl;
    return 0;
}
""",
            },
            {
                "title": "C++ | Unique values medium",
                "language": "cpp",
                "difficulty": "medium",
                "code_body": """#include <bits/stdc++.h>
using namespace std;

int main() {
    vector<int> v = {1,2,2,3,4,4,5};
    sort(v.begin(), v.end());
    v.erase(unique(v.begin(), v.end()), v.end());
    for (int x : v) cout << x << " ";
    return 0;
}
""",
            },
            {
                "title": "C++ | Dijkstra hard",
                "language": "cpp",
                "difficulty": "hard",
                "code_body": """#include <bits/stdc++.h>
using namespace std;

vector<vector<pair<int,int>>> g;
vector<int> dist;

void dijkstra(int s) {
    priority_queue<pair<int,int>, vector<pair<int,int>>, greater<>> pq;
    dist[s] = 0; pq.push({0, s});
    while (!pq.empty()) {
        auto [d, u] = pq.top(); pq.pop();
        if (d != dist[u]) continue;
        for (auto [v, w] : g[u]) {
            if (dist[v] > d + w) {
                dist[v] = d + w;
                pq.push({dist[v], v});
            }
        }
    }
}

int main() {
    int n = 4;
    g.assign(n, {});
    g[0].push_back({1, 2}); g[0].push_back({2, 5});
    g[1].push_back({2, 1}); g[1].push_back({3, 4});
    g[2].push_back({3, 1});
    dist.assign(n, 1e9);
    dijkstra(0);
    for (int d : dist) cout << d << " ";
    return 0;
}
""",
            },
            # Java
            {
                "title": "Java | Stream filter easy",
                "language": "java",
                "difficulty": "easy",
                "code_body": """import java.util.*;
import java.util.stream.*;

public class Main {
    public static void main(String[] args) {
        List<Integer> nums = Arrays.asList(1,2,3,4,5,6);
        List<Integer> evens = nums.stream()
            .filter(n -> n % 2 == 0)
            .collect(Collectors.toList());
        System.out.println(evens);
    }
}
""",
            },
            {
                "title": "Java | Optional usage medium",
                "language": "java",
                "difficulty": "medium",
                "code_body": """import java.util.*;

public class Main {
    static Optional<String> findName(List<String> names, String query) {
        return names.stream().filter(n -> n.equalsIgnoreCase(query)).findFirst();
    }
    public static void main(String[] args) {
        var names = List.of("Alice", "Bob", "Charlie");
        System.out.println(findName(names, "bob").orElse("Not found"));
    }
}
""",
            },
            {
                "title": "Java | LRU cache hard",
                "language": "java",
                "difficulty": "hard",
                "code_body": """import java.util.*;

class LRU<K, V> extends LinkedHashMap<K, V> {
    private final int capacity;
    LRU(int capacity) {
        super(capacity, 0.75f, true);
        this.capacity = capacity;
    }
    protected boolean removeEldestEntry(Map.Entry<K, V> eldest) {
        return size() > capacity;
    }
}

public class Main {
    public static void main(String[] args) {
        LRU<Integer, String> cache = new LRU<>(3);
        cache.put(1, "a"); cache.put(2, "b"); cache.put(3, "c");
        cache.get(1); cache.put(4, "d");
        System.out.println(cache.keySet()); // prints [3, 1, 4]
    }
}
""",
            },
        ]

        created = 0
        for snippet in snippets:
            obj, was_created = CodeSnippet.objects.get_or_create(
                title=snippet["title"],
                defaults={
                    "language": snippet["language"],
                    "difficulty": snippet["difficulty"],
                    "code_body": snippet["code_body"],
                },
            )
            if was_created:
                created += 1
                self.stdout.write(self.style.SUCCESS(f"Created: {obj.title}"))
            else:
                self.stdout.write(self.style.WARNING(f"Skipped (exists): {obj.title}"))

        self.stdout.write(self.style.SUCCESS(f"\nDone. Created {created} new code snippets."))

