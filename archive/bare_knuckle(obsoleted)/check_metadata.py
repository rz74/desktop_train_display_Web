"""Explore underground library structure"""
from underground import metadata
import dir

print("Metadata attributes:")
print(dir(metadata))

# Try to access feeds
if hasattr(metadata, 'feeds'):
    print(f"\nFeeds: {metadata.feeds}")
    
# Try to get routes
if hasattr(metadata, 'routes'):
    print(f"\nRoutes (first 10):")
    for i, (k, v) in enumerate(list(metadata.routes.items())[:10]):
        print(f"  {k}: {v}")
