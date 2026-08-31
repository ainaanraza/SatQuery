import argparse
from satquery.agent import SatQueryAgent

def main():
    parser = argparse.ArgumentParser(description="SatQuery AI - Agentic CLI")
    parser.add_argument("--query", required=True, help="Natural language query")
    parser.add_argument("--image", help="Path to raster file")
    parser.add_argument("--image-before", help="Path to before raster file")
    parser.add_argument("--image-after", help="Path to after raster file")
    args = parser.parse_args()
    
    agent = SatQueryAgent()
    inputs = []
    if args.image:
        inputs.append(args.image)
    if args.image_before:
        inputs.append(args.image_before)
    if args.image_after:
        inputs.append(args.image_after)
        
    try:
        response = agent.run(query=args.query, inputs=inputs)
        print("\nSatQuery AI — Agent Response\n")
        print(f"Query: {args.query}")
        print(f"Answer: {response.answer}")
        print("\nEvidence:")
        for ev in response.evidence:
            print(f" - [{ev.tool}] Source: {ev.source} (Type: {ev.source_type})")
        
        if response.limitations:
            print("\nLimitations:")
            for lim in response.limitations:
                print(f" - {lim}")
                
    except Exception as e:
        print(f"Agent failed with error: {e}")

if __name__ == "__main__":
    main()
