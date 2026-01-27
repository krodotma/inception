#!/usr/bin/env python3
"""
Seed script: Populates LMDB with OAuth/Security domain knowledge graph.

This creates a rich demonstration dataset including:
- Entities with temporal validity
- Claims with multi-source credibility
- Procedures with steps
- Knowledge gaps
- Sources with credibility scores

Usage:
    cd /Users/kroma/inceptional
    uv run python scripts/seed_knowledge.py
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def get_lmdb_env():
    """Get LMDB environment for writing."""
    import lmdb
    
    db_path = os.path.expanduser("~/.inception/knowledge.lmdb")
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    return lmdb.open(
        db_path,
        map_size=10 * 1024 * 1024 * 1024,  # 10GB
        max_dbs=10,
        subdir=True
    )


# =============================================================================
# SEED DATA
# =============================================================================

ENTITIES = [
    {
        "id": "oauth2",
        "name": "OAuth 2.0",
        "type": "protocol",
        "description": "Industry-standard authorization framework enabling third-party applications to obtain limited access to user accounts",
        "valid_from": "2012-10-01T00:00:00Z",
        "valid_until": None,
        "aliases": ["OAuth", "OAuth2"],
    },
    {
        "id": "pkce",
        "name": "PKCE",
        "type": "extension",
        "description": "Proof Key for Code Exchange - prevents authorization code interception attacks",
        "valid_from": "2015-09-01T00:00:00Z", 
        "valid_until": None,
        "aliases": ["Proof Key for Code Exchange", "RFC 7636"],
    },
    {
        "id": "jwt",
        "name": "JSON Web Token",
        "type": "standard",
        "description": "Compact, URL-safe means of representing claims to be transferred between two parties",
        "valid_from": "2015-05-01T00:00:00Z",
        "valid_until": None,
        "aliases": ["JWT", "RFC 7519"],
    },
    {
        "id": "bearer-token",
        "name": "Bearer Token",
        "type": "token_type",
        "description": "Access token type where possession is sufficient for access",
        "valid_from": "2012-10-01T00:00:00Z",
        "valid_until": None,
    },
    {
        "id": "refresh-token",
        "name": "Refresh Token",
        "type": "token_type", 
        "description": "Long-lived token used to obtain new access tokens without re-authentication",
        "valid_from": "2012-10-01T00:00:00Z",
        "valid_until": None,
    },
    {
        "id": "authorization-code",
        "name": "Authorization Code Grant",
        "type": "grant_type",
        "description": "OAuth 2.0 grant type for server-side applications with secure client secret storage",
        "valid_from": "2012-10-01T00:00:00Z",
        "valid_until": None,
    },
    {
        "id": "implicit-grant",
        "name": "Implicit Grant",
        "type": "grant_type",
        "description": "OAuth 2.0 grant type for browser-based applications (DEPRECATED)",
        "valid_from": "2012-10-01T00:00:00Z",
        "valid_until": "2021-08-01T00:00:00Z",  # Deprecated in OAuth 2.1
    },
    {
        "id": "client-credentials",
        "name": "Client Credentials Grant",
        "type": "grant_type",
        "description": "OAuth 2.0 grant type for machine-to-machine authentication",
        "valid_from": "2012-10-01T00:00:00Z",
        "valid_until": None,
    },
    {
        "id": "openid-connect",
        "name": "OpenID Connect",
        "type": "protocol",
        "description": "Identity layer on top of OAuth 2.0 for authentication",
        "valid_from": "2014-02-26T00:00:00Z",
        "valid_until": None,
        "aliases": ["OIDC"],
    },
    {
        "id": "authorization-server",
        "name": "Authorization Server",
        "type": "component",
        "description": "Server that issues access tokens after authenticating the resource owner",
        "valid_from": "2012-10-01T00:00:00Z",
        "valid_until": None,
    },
    {
        "id": "resource-server",
        "name": "Resource Server",
        "type": "component",
        "description": "Server hosting protected resources, accepting access tokens",
        "valid_from": "2012-10-01T00:00:00Z",
        "valid_until": None,
    },
    {
        "id": "lmdb",
        "name": "LMDB",
        "type": "database",
        "description": "Lightning Memory-Mapped Database - high-performance embedded key-value store",
        "valid_from": "2011-01-01T00:00:00Z",
        "valid_until": None,
        "aliases": ["Lightning Memory-Mapped Database"],
    },
]

CLAIMS = [
    {
        "id": "c1",
        "statement": "OAuth 2.0 is an authorization framework, not an authentication protocol",
        "entity_ids": ["oauth2"],
        "source_ids": ["rfc6749", "oauth-net"],
        "confidence": 0.98,
        "valid_from": "2012-10-01T00:00:00Z",
        "valid_until": None,
    },
    {
        "id": "c2", 
        "statement": "PKCE prevents authorization code interception attacks in public clients",
        "entity_ids": ["pkce", "oauth2", "authorization-code"],
        "source_ids": ["rfc7636", "oauth-net"],
        "confidence": 0.97,
        "valid_from": "2015-09-01T00:00:00Z",
        "valid_until": None,
    },
    {
        "id": "c3",
        "statement": "The Implicit Grant is deprecated and should not be used for new applications",
        "entity_ids": ["implicit-grant", "oauth2"],
        "source_ids": ["oauth21-draft", "oauth-net"],
        "confidence": 0.95,
        "valid_from": "2021-08-01T00:00:00Z",
        "valid_until": None,
    },
    {
        "id": "c4",
        "statement": "JWT tokens should have short expiration times (15 minutes or less)",
        "entity_ids": ["jwt", "bearer-token"],
        "source_ids": ["jwt-best-practices", "auth0-docs"],
        "confidence": 0.85,
        "valid_from": "2018-01-01T00:00:00Z",
        "valid_until": None,
    },
    {
        "id": "c5",
        "statement": "Refresh tokens should be rotated on each use to limit replay attacks",
        "entity_ids": ["refresh-token", "oauth2"],
        "source_ids": ["rfc6749", "oauth-security-bcp"],
        "confidence": 0.92,
        "valid_from": "2020-01-01T00:00:00Z",
        "valid_until": None,
    },
    {
        "id": "c6",
        "statement": "OpenID Connect adds an ID token containing user identity claims to OAuth 2.0",
        "entity_ids": ["openid-connect", "oauth2", "jwt"],
        "source_ids": ["oidc-spec", "auth0-docs"],
        "confidence": 0.99,
        "valid_from": "2014-02-26T00:00:00Z",
        "valid_until": None,
    },
    {
        "id": "c7",
        "statement": "Authorization servers must validate redirect URIs to prevent open redirect attacks",
        "entity_ids": ["authorization-server", "oauth2"],
        "source_ids": ["oauth-security-bcp", "rfc6749"],
        "confidence": 0.96,
        "valid_from": "2012-10-01T00:00:00Z",
        "valid_until": None,
    },
    {
        "id": "c8",
        "statement": "LMDB provides ACID transactions with zero-copy reads for maximum performance",
        "entity_ids": ["lmdb"],
        "source_ids": ["lmdb-docs"],
        "confidence": 0.99,
        "valid_from": "2011-01-01T00:00:00Z",
        "valid_until": None,
    },
]

PROCEDURES = [
    {
        "id": "proc-oauth-pkce",
        "title": "Implement OAuth 2.0 with PKCE",
        "description": "Secure authorization code flow for public clients",
        "entity_ids": ["oauth2", "pkce", "authorization-code"],
        "steps": [
            "Generate cryptographically random code_verifier (43-128 chars)",
            "Create code_challenge = BASE64URL(SHA256(code_verifier))",
            "Redirect user to authorization endpoint with code_challenge",
            "User authenticates and authorizes the application",
            "Receive authorization code at redirect_uri",
            "Exchange code for tokens, including code_verifier",
            "Store refresh token securely, use access token for API calls",
        ],
    },
    {
        "id": "proc-jwt-validation",
        "title": "Validate JWT Access Token",
        "description": "Proper JWT validation for resource servers",
        "entity_ids": ["jwt", "resource-server"],
        "steps": [
            "Extract JWT from Authorization header (Bearer scheme)",
            "Verify signature using issuer's public key (JWKS)",
            "Check 'exp' claim to ensure token is not expired",
            "Validate 'iss' claim matches expected authorization server",
            "Validate 'aud' claim includes this resource server",
            "Check 'scope' or 'permissions' for required access",
            "Extract user identity from 'sub' claim if needed",
        ],
    },
    {
        "id": "proc-token-refresh",
        "title": "Refresh Access Token Workflow",
        "description": "Obtain new access token using refresh token",
        "entity_ids": ["refresh-token", "bearer-token", "authorization-server"],
        "steps": [
            "Detect access token expiration (401 response or exp check)",
            "Send POST to token endpoint with grant_type=refresh_token",
            "Include current refresh_token in request body",
            "Receive new access_token (and optionally new refresh_token)",
            "Update stored tokens in secure storage",
            "Retry original failed request with new access token",
        ],
    },
]

GAPS = [
    {
        "id": "gap-1",
        "description": "What are the security implications of storing JWTs in localStorage vs httpOnly cookies?",
        "priority": "high",
        "gap_type": "missing_knowledge",
        "related_entities": ["jwt", "bearer-token"],
        "attempts": 0,
    },
    {
        "id": "gap-2", 
        "description": "How does OAuth 2.1 differ from OAuth 2.0?",
        "priority": "medium",
        "gap_type": "outdated",
        "related_entities": ["oauth2", "implicit-grant", "pkce"],
        "attempts": 0,
    },
    {
        "id": "gap-3",
        "description": "What is the relationship between DPoP and PKCE?",
        "priority": "low",
        "gap_type": "missing_connection",
        "related_entities": ["pkce", "oauth2"],
        "attempts": 0,
    },
]

SOURCES = [
    {
        "id": "rfc6749",
        "title": "RFC 6749 - The OAuth 2.0 Authorization Framework",
        "url": "https://datatracker.ietf.org/doc/html/rfc6749",
        "type": "specification",
        "credibility": 0.99,
        "date": "2012-10-01",
    },
    {
        "id": "rfc7636",
        "title": "RFC 7636 - Proof Key for Code Exchange (PKCE)",
        "url": "https://datatracker.ietf.org/doc/html/rfc7636",
        "type": "specification",
        "credibility": 0.99,
        "date": "2015-09-01",
    },
    {
        "id": "oauth-net",
        "title": "OAuth.net - Community Resources",
        "url": "https://oauth.net",
        "type": "educational",
        "credibility": 0.92,
        "date": "2024-01-01",
    },
    {
        "id": "auth0-docs",
        "title": "Auth0 Documentation",
        "url": "https://auth0.com/docs",
        "type": "documentation",
        "credibility": 0.88,
        "date": "2024-01-01",
    },
    {
        "id": "oauth-security-bcp",
        "title": "OAuth 2.0 Security Best Current Practice",
        "url": "https://datatracker.ietf.org/doc/html/draft-ietf-oauth-security-topics",
        "type": "specification",
        "credibility": 0.97,
        "date": "2023-01-01",
    },
    {
        "id": "lmdb-docs",
        "title": "LMDB Documentation",
        "url": "https://lmdb.readthedocs.io",
        "type": "documentation",
        "credibility": 0.95,
        "date": "2023-01-01",
    },
]


def seed_database():
    """Seed LMDB with knowledge graph data."""
    print("🌱 Seeding Inception knowledge database...")
    
    env = get_lmdb_env()
    
    with env.begin(write=True) as txn:
        # Create databases
        entities_db = env.open_db(b'entities', txn=txn, create=True)
        claims_db = env.open_db(b'claims', txn=txn, create=True)
        procedures_db = env.open_db(b'procedures', txn=txn, create=True)
        gaps_db = env.open_db(b'gaps', txn=txn, create=True)
        sources_db = env.open_db(b'sources', txn=txn, create=True)
        
        # Seed entities
        for entity in ENTITIES:
            txn.put(
                entity['id'].encode(),
                json.dumps(entity).encode(),
                db=entities_db
            )
        print(f"  ✓ {len(ENTITIES)} entities")
        
        # Seed claims
        for claim in CLAIMS:
            txn.put(
                claim['id'].encode(),
                json.dumps(claim).encode(),
                db=claims_db
            )
        print(f"  ✓ {len(CLAIMS)} claims")
        
        # Seed procedures
        for proc in PROCEDURES:
            txn.put(
                proc['id'].encode(),
                json.dumps(proc).encode(),
                db=procedures_db
            )
        print(f"  ✓ {len(PROCEDURES)} procedures")
        
        # Seed gaps
        for gap in GAPS:
            txn.put(
                gap['id'].encode(),
                json.dumps(gap).encode(),
                db=gaps_db
            )
        print(f"  ✓ {len(GAPS)} gaps")
        
        # Seed sources
        for source in SOURCES:
            txn.put(
                source['id'].encode(),
                json.dumps(source).encode(),
                db=sources_db
            )
        print(f"  ✓ {len(SOURCES)} sources")
    
    env.close()
    print("\n✅ Database seeded successfully!")
    print(f"   Location: ~/.inception/knowledge.lmdb")


if __name__ == "__main__":
    seed_database()
