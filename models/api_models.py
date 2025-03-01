from dataclasses import dataclass
from typing import List, Optional

@dataclass
class QueryRequest:
    query: str
    context: Optional[List[str]] = None

@dataclass
class QueryResponse:
    answer: str
    context: str
    relevant_files: List[str]
