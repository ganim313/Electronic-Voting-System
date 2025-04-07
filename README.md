# Electronic Voting System

This repository contains an Electronic Voting System designed to facilitate secure and anonymous voting using advanced cryptographic protocols. The system ensures voter privacy, integrity of votes, and universal verifiability through a combination of homomorphic encryption, zero-knowledge proofs, and a threshold decryption scheme.

## Features

- Secure and anonymous voting
- Voter privacy and vote integrity
- Universal verifiability
- Homomorphic encryption
- Zero-knowledge proofs
- Threshold decryption scheme
- SSL/TLS connections for secure communication

## System Architecture

The system is implemented using a distributed architecture with the following components:

1. **App Server**: Hosts the main application (`app.py`).
2. **Bulletin Board**: Stores public information about the election.
3. **Registry**: Manages voter registration and authentication.
4. **Tally Servers**: Collects and submit keys to bulletin board for tallying votes.
5. **Trusted Authority**: Initiate Election and  issue keys to different actors involved in this.

Each component is hosted on a separate server and communicates using SSL/TLS connections to ensure secure data transmission.
### Prerequisites

- Python 3.x
- SSL/TLS certificates for secure communication
- Dependencies listed in `requirements.txt`

### Voting

1. Voters can log in using their credentials.
2. The system allows voting for two options:
    - Party A or Party B
    - Yes or No
3. Votes are securely transmitted and tallied.

## Security

- All communications are secured using SSL/TLS.
- The system employs advanced cryptographic protocols to ensure the integrity and privacy of votes.
- Voter authentication and registration are managed securely by the Registry component.

