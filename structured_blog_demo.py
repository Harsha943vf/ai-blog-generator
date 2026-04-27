#!/usr/bin/env python3
"""
Structured Blog Generator - Demo Script
Demonstrates the strict 5-step structured pipeline

Usage:
    python structured_blog_demo.py "Your blog topic here"
"""

import sys
import logging
from backend.structured_service import generate_structured_blog

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("structured_demo")


def main():
    if len(sys.argv) < 2:
        print("Usage: python structured_blog_demo.py <topic>")
        print("Example: python structured_blog_demo.py 'Quantum Computing Explained'")
        sys.exit(1)
    
    topic = " ".join(sys.argv[1:])
    print(f"\n{'='*70}")
    print(f"STRUCTURED BLOG GENERATOR")
    print(f"{'='*70}")
    print(f"Topic: {topic}\n")
    
    result = generate_structured_blog(topic)
    
    if result["status"] == "error":
        print(f"❌ ERROR: {result['error']}")
        print(f"Elapsed: {result['elapsed_seconds']}s\n")
        sys.exit(1)
    
    # Display all outputs
    print("\n" + "="*70)
    print("1️⃣  ROUTER OUTPUT")
    print("="*70)
    print(result["router_output"])
    
    print("\n" + "="*70)
    print("2️⃣  PLANNER OUTPUT")
    print("="*70)
    print(result["planner_output"])
    
    print("\n" + "="*70)
    print("3️⃣  RESEARCH OUTPUT")
    print("="*70)
    print(result["research_output"])
    
    print("\n" + "="*70)
    print("4️⃣  GENERATOR OUTPUT (first 800 chars)")
    print("="*70)
    generator = result["generator_output"]
    print(generator[:800] + ("..." if len(generator) > 800 else ""))
    
    print("\n" + "="*70)
    print("5️⃣  FINAL EDITOR OUTPUT (first 800 chars)")
    print("="*70)
    final = result["final_blog"]
    print(final[:800] + ("..." if len(final) > 800 else ""))
    
    print("\n" + "="*70)
    print(f"✅ COMPLETED in {result['elapsed_seconds']}s")
    print("="*70)
    print(f"Total sections: {len(result['sections'])}")
    print(f"Sections: {', '.join(result['sections'])}")
    
    # Save full output to file
    output_file = "structured_blog_output.txt"
    with open(output_file, "w") as f:
        f.write("="*70 + "\n")
        f.write("COMPLETE STRUCTURED PIPELINE OUTPUT\n")
        f.write("="*70 + "\n\n")
        f.write("STEP 1: ROUTER\n")
        f.write("-"*70 + "\n")
        f.write(result["router_output"] + "\n\n")
        f.write("STEP 2: PLANNER\n")
        f.write("-"*70 + "\n")
        f.write(result["planner_output"] + "\n\n")
        f.write("STEP 3: RESEARCH\n")
        f.write("-"*70 + "\n")
        f.write(result["research_output"] + "\n\n")
        f.write("STEP 4: GENERATOR\n")
        f.write("-"*70 + "\n")
        f.write(result["generator_output"] + "\n\n")
        f.write("STEP 5: EDITOR\n")
        f.write("-"*70 + "\n")
        f.write(result["final_blog"] + "\n\n")
        f.write("="*70 + "\n")
        f.write(f"TOTAL TIME: {result['elapsed_seconds']}s\n")
        f.write("="*70 + "\n")
    
    print(f"\n📄 Full output saved to: {output_file}")


if __name__ == "__main__":
    main()
