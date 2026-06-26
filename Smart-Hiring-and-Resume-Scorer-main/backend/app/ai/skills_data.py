# Comprehensive skill dictionary with synonyms
SKILL_SYNONYMS = {
    # Programming Languages
    "python": ["python3", "py"],
    "javascript": ["js", "ecmascript", "es6", "es2015"],
    "typescript": ["ts"],
    "java": ["java8", "java11", "java17"],
    "golang": ["go lang", "go programming"],
    "rust": ["rust lang"],
    "c++": ["cpp", "c plus plus"],
    "c#": ["csharp", "c sharp", ".net c#"],
    "ruby": ["ruby on rails"],
    "php": ["php7", "php8"],
    "swift": ["swift ui"],
    "kotlin": [],
    "scala": [],
    "r": ["r programming", "r language"],
    
    # Frontend
    "react": ["reactjs", "react.js", "react native"],
    "vue": ["vuejs", "vue.js", "vue3"],
    "angular": ["angularjs", "angular2+"],
    "nextjs": ["next.js", "next js"],
    "svelte": ["sveltekit"],
    "html": ["html5"],
    "css": ["css3", "stylesheets"],
    "tailwind": ["tailwindcss", "tailwind css"],
    "webpack": ["bundler"],
    "graphql": ["graph ql"],
    
    # Backend
    "nodejs": ["node.js", "node js", "express", "expressjs"],
    "fastapi": ["fast api"],
    "django": ["django rest framework", "drf"],
    "flask": [],
    "spring": ["spring boot", "spring framework"],
    "rails": ["ruby on rails", "ror"],
    "laravel": [],
    "nestjs": ["nest.js"],
    
    # Databases
    "postgresql": ["postgres", "psql"],
    "mysql": ["mariadb"],
    "mongodb": ["mongo", "mongoose"],
    "redis": ["redis cache"],
    "elasticsearch": ["elastic", "elk stack"],
    "sqlite": [],
    "oracle": ["oracle db"],
    "sql": ["structured query language", "t-sql", "pl/sql"],
    "nosql": [],
    "dynamodb": ["dynamo db"],
    "cassandra": [],
    
    # Cloud & DevOps
    "aws": ["amazon web services", "amazon aws", "ec2", "s3", "lambda"],
    "gcp": ["google cloud", "google cloud platform"],
    "azure": ["microsoft azure"],
    "docker": ["containerization", "containers"],
    "kubernetes": ["k8s", "k8"],
    "terraform": ["infrastructure as code"],
    "ansible": [],
    "jenkins": ["ci/cd jenkins"],
    "github actions": ["gh actions"],
    "gitlab ci": ["gitlab pipelines"],
    "ci/cd": ["continuous integration", "continuous deployment", "continuous delivery"],
    "linux": ["ubuntu", "debian", "centos", "unix"],
    "nginx": ["web server"],
    
    # AI/ML
    "machine learning": ["ml", "supervised learning", "unsupervised learning"],
    "deep learning": ["dl", "neural networks"],
    "tensorflow": ["tf", "tf2"],
    "pytorch": ["torch"],
    "scikit-learn": ["sklearn", "scikit learn"],
    "nlp": ["natural language processing", "text processing"],
    "computer vision": ["cv", "image processing"],
    "hugging face": ["transformers", "huggingface"],
    "llm": ["large language model", "gpt", "openai"],
    "data science": ["data analysis", "analytics"],
    "pandas": ["dataframe"],
    "numpy": [],
    "spark": ["apache spark", "pyspark"],
    
    # Soft Skills / Management
    "agile": ["scrum", "kanban", "sprint planning"],
    "leadership": ["team lead", "tech lead", "leading teams"],
    "mentoring": ["mentorship", "coaching engineers"],
    "project management": ["pm", "project planning"],
    "communication": ["stakeholder communication", "cross-functional"],
    "problem solving": ["analytical thinking", "critical thinking"],
    
    # Testing
    "unit testing": ["unittest", "pytest", "junit"],
    "integration testing": [],
    "tdd": ["test driven development"],
    "selenium": ["test automation"],
    
    # Security
    "cybersecurity": ["security", "infosec"],
    "owasp": ["security best practices"],
    "jwt": ["json web token", "authentication"],
    "oauth": ["oauth2", "sso"],
    
    # Methodologies
    "rest api": ["restful api", "rest", "api design"],
    "microservices": ["micro services", "service mesh"],
    "system design": ["distributed systems", "architecture"],
    "git": ["version control", "github", "gitlab", "bitbucket"],
}

# Build reverse lookup
SKILL_LOOKUP = {}
for canonical, synonyms in SKILL_SYNONYMS.items():
    SKILL_LOOKUP[canonical] = canonical
    for syn in synonyms:
        SKILL_LOOKUP[syn] = canonical

# All canonical skills list
ALL_SKILLS = list(SKILL_SYNONYMS.keys())

def normalize_skill(skill: str) -> str:
    """Normalize a skill name to canonical form."""
    skill_lower = skill.lower().strip()
    return SKILL_LOOKUP.get(skill_lower, skill_lower)

def get_all_variants(skill: str) -> list:
    """Get all variants of a skill."""
    canonical = normalize_skill(skill)
    return [canonical] + SKILL_SYNONYMS.get(canonical, [])
