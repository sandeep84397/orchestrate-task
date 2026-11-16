# M3 #155 Feed thumbnails
updated: 2026-11-16T14:05
branch: x @ y   base: 8d1e0b4
goals (plan v1): M3.g1 ✓ · M3.g2 ✓ · M3.g3 ✓ · M3.g4 ▸ · M3.g5
goal: M3.g4 Fallback when the thumbnail is empty
state: red
prep: none
evidence:
- g1: milestones/M3/evidence/g1/
lease: none
next: continue
ack: #31
reply: none

BLOCKED M3.g4-1
blocked: write the fallback test against the real response
evidence: milestones/M3/evidence/g4/real-sample.json
diagnosis: thumbnail is generated after the feed lists the video — verified (12 real responses)
need: treat empty as not ready, or change the backend? — recommend: treat empty as not ready
class: contract
meanwhile: STOPPED
