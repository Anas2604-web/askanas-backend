import os
import glob
from dataclasses import dataclass
import re
from fastembed import TextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct

@dataclass
class ProjectChunk:
    content: str
    project_title: str
    section_title: str
    source_file: str


def parse_markdown_sections(filepath: str) -> dict[str, str]:
    """Split a markdown file into {section_title: section_text} by '## ' headers."""
    sections: dict[str, str] = {}
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except OSError:
        return sections

    content = content.replace("\r\n", "\n")
    header_pattern = re.compile(r"^##\s+(.+)$", re.MULTILINE)
    matches = list(header_pattern.finditer(content))

    first_section_start = matches[0].start() if matches else len(content)
    intro_text = content[:first_section_start].strip()
    if intro_text:
        sections["Introduction/Overview"] = intro_text

    for i, match in enumerate(matches):
        section_title = match.group(1)
        start_pos = match.end()
        end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        section_text = content[start_pos:end_pos].strip()
        if section_text:
            sections[section_title] = section_text

    return sections


def chunk_section(section_title: str, section_text: str) -> list[str]:
    """Return a section as one chunk, or split it by paragraph if it's too long."""
    max_chunk_size = 1500
    if len(section_text) <= max_chunk_size:
        return [section_text]

    paragraphs = section_text.split("\n\n")
    chunks = []
    current_chunk = ""
    for para in paragraphs:
        if len(current_chunk) + len(para) > max_chunk_size:
            chunks.append(current_chunk)
            current_chunk = para
        else:
            current_chunk += "\n\n" + para if current_chunk else para
    if current_chunk:
        chunks.append(current_chunk)
    return chunks


def build_chunks_for_project(filepath: str, project_title: str) -> list[ProjectChunk]:
    """Parse a project doc into sections, chunk each section, attach metadata."""
    project_chunks: list[ProjectChunk] = []
    sections = parse_markdown_sections(filepath)
    for section_title, section_text in sections.items():
        text_chunks = chunk_section(section_title, section_text)
        for chunk_text in text_chunks:
            project_chunks.append(
                ProjectChunk(
                    content=chunk_text,
                    section_title=section_title,
                    project_title=project_title,
                    source_file=filepath,
                )
            )
    return project_chunks


def embed_chunks(texts: list[str], batch_size: int = 32) -> list[list[float]]:
    """Embed a list of texts into 384-dim vectors using fastembed."""
    model = TextEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
    return list(model.embed(texts, batch_size=batch_size))


def load_all_project_chunks(data_dir: str = "data/projects") -> list[ProjectChunk]:
    """Loop over every .md file in data_dir and chunk it, using the filename
    (minus extension) as the project_title."""
    all_chunks: list[ProjectChunk] = []
    md_files = glob.glob(os.path.join(data_dir, "*.md"))

    for filepath in md_files:
        project_title = os.path.splitext(os.path.basename(filepath))[0]
        all_chunks.extend(build_chunks_for_project(filepath, project_title))

    return all_chunks



if __name__ == "__main__":
    all_chunks = load_all_project_chunks()
    print(f"Loaded {len(all_chunks)} chunks from {len(set(c.project_title for c in all_chunks))} project docs.")