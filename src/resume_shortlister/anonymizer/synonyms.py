import re
from typing import Dict, Set, List

# Comprehensive mapping of canonical skill -> recognized variations and synonyms
SKILL_SYNONYMS: Dict[str, Set[str]] = {
    # Frontend & Web
    "react": {"react", "react.js", "reactjs", "react-js"},
    "vue": {"vue", "vue.js", "vuejs"},
    "angular": {"angular", "angular.js", "angularjs", "angular 2+"},
    "svelte": {"svelte", "sveltekit"},
    "next.js": {"next.js", "nextjs", "next"},
    "nuxt": {"nuxt", "nuxt.js", "nuxtjs"},
    "html": {"html", "html5"},
    "css": {"css", "css3", "sass", "scss", "less"},
    "tailwind": {"tailwind", "tailwindcss", "tailwind-css"},
    "redux": {"redux", "redux toolkit", "rtk"},
    
    # Programming Languages
    "python": {"python", "py", "python3"},
    "typescript": {"typescript", "ts"},
    "javascript": {"javascript", "js", "ecmascript", "es6"},
    "java": {"java", "core java", "java 8", "java 11", "java 17"},
    "c++": {"c++", "cpp"},
    "c#": {"c#", "csharp", "c-sharp", ".net"},
    "golang": {"go", "golang"},
    "rust": {"rust"},
    "ruby": {"ruby", "ruby on rails", "rails"},
    "php": {"php", "laravel"},
    "swift": {"swift", "swiftui"},
    "kotlin": {"kotlin"},
    "scala": {"scala"},

    # Backend Frameworks
    "fastapi": {"fastapi", "fast-api", "fast api"},
    "django": {"django", "django-rest-framework", "drf"},
    "flask": {"flask"},
    "node": {"node", "node.js", "nodejs"},
    "express": {"express", "express.js", "expressjs"},
    "nestjs": {"nestjs", "nest.js", "nest"},
    "spring boot": {"spring boot", "spring", "spring framework", "spring-boot"},

    # Databases & Storage
    "postgresql": {"postgresql", "postgres", "psql"},
    "mysql": {"mysql", "my-sql"},
    "sqlite": {"sqlite", "sqlite3"},
    "mongodb": {"mongodb", "mongo"},
    "redis": {"redis"},
    "elasticsearch": {"elasticsearch", "elastic search", "opensearch"},
    "cassandra": {"cassandra"},
    "dynamodb": {"dynamodb", "dynamo"},
    "snowflake": {"snowflake"},
    "sql": {"sql", "rdbms", "relational database", "relational databases", "t-sql", "pl/sql"},

    # DevOps, Cloud & Containers
    "docker": {"docker", "dockerfile", "containerization", "containers"},
    "kubernetes": {"kubernetes", "k8s"},
    "ci/cd": {"ci/cd", "cicd", "continuous integration", "continuous deployment", "github actions", "gitlab ci", "jenkins", "circleci"},
    "aws": {"aws", "amazon web services", "ec2", "s3", "lambda", "rds", "cloudformation"},
    "gcp": {"gcp", "google cloud", "google cloud platform", "bigquery"},
    "azure": {"azure", "microsoft azure"},
    "terraform": {"terraform", "iac", "infrastructure as code"},
    "ansible": {"ansible"},
    "prometheus": {"prometheus", "grafana", "monitoring"},
    "linux": {"linux", "ubuntu", "debian", "unix", "bash", "shell scripting"},
    "git": {"git", "github", "gitlab", "version control"},

    # Messaging & Distributed Systems
    "kafka": {"kafka", "apache kafka"},
    "rabbitmq": {"rabbitmq", "rabbit mq"},
    "microservices": {"microservices", "micro-services", "service-oriented architecture", "distributed systems"},
    "rest api": {"rest api", "restful api", "rest apis", "restful", "rest"},
    "graphql": {"graphql", "gql"},
    "grpc": {"grpc"},

    # AI, ML & Data Science
    "machine learning": {"machine learning", "ml", "statistical learning"},
    "deep learning": {"deep learning", "dl", "neural networks"},
    "nlp": {"nlp", "natural language processing", "text processing", "sentiment analysis"},
    "llm": {"llm", "llms", "large language model", "large language models", "generative ai", "genai"},
    "rag": {"rag", "retrieval augmented generation", "vector search"},
    "langchain": {"langchain", "llamaindex"},
    "pytorch": {"pytorch", "torch"},
    "tensorflow": {"tensorflow", "tf", "keras"},
    "scikit-learn": {"scikit-learn", "sklearn"},
    "pandas": {"pandas"},
    "numpy": {"numpy"},
    "spark": {"spark", "pyspark", "apache spark"},
    "airflow": {"airflow", "apache airflow"},

    # Methodologies
    "agile": {"agile", "scrum", "kanban", "sprints"}
}

def canonicalize_skill(skill: str) -> str:
    """
    Returns the canonical lowercase representation of a skill if found in synonym dictionary,
    otherwise returns the trimmed lowercase string.
    """
    clean_skill = skill.strip().lower()
    for canonical, variations in SKILL_SYNONYMS.items():
        if clean_skill == canonical or clean_skill in variations:
            return canonical
    return clean_skill

def are_skills_equivalent(skill_a: str, skill_b: str) -> bool:
    """
    Checks if two skill strings represent the same skill via synonym mapping.
    """
    canon_a = canonicalize_skill(skill_a)
    canon_b = canonicalize_skill(skill_b)
    if canon_a == canon_b:
        return True
    
    # Check if either appears in the other's synonym set
    for canonical, variations in SKILL_SYNONYMS.items():
        if (skill_a.lower() in variations or skill_a.lower() == canonical) and \
           (skill_b.lower() in variations or skill_b.lower() == canonical):
            return True
            
    return False

def match_skills_in_text(text: str, target_skills: List[str]) -> List[str]:
    """
    Checks which target skills appear in the given text using regex and synonym matching.
    Returns list of matched target skills in their original target string casing.
    """
    text_lower = text.lower()
    matched = []
    
    for target in target_skills:
        canonical = canonicalize_skill(target)
        variations = set(SKILL_SYNONYMS.get(canonical, set()))
        variations.add(target.lower())
        variations.add(canonical)
        
        found = False
        for var in variations:
            # Word boundary regex ensuring symbols like c++ or .net are handled
            escaped_var = re.escape(var)
            pattern = r'(?<![a-zA-Z0-9_\-\.])' + escaped_var + r'(?![a-zA-Z0-9_\-\.])'
            if re.search(pattern, text_lower):
                matched.append(target)
                found = True
                break
                
    return matched
