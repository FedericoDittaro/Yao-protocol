This project covers an example of Secure Multi-Party Computation (MPC) according to Yao’s protocol and it's part of the course "Introduction to Cybersecurity" held at the
Alpen-Adria-Universität of Klagenfurt. This protocol allows two parties (Alice and Bob) with private inputs to compute a joint function of their inputs while ensuring that nothing but the output is learned. For example if Alice knows x and Bob knows y, they should only learn the result of f(x,y). MPC is based on the following ideas:

- Privacy: ensuring that nothing but the output is learned;
- Correctness: ensuring that the output is correctly computed.

Properties should be guaranteed even in the face of adversarial behavior:

- Semi-honest: adversary running the correct software cannot learn anything;
- Malicious: adversary running any software cannot learn anything (even if they know all the protocols, design and so on).

This goal is achieved by using a boolean circuit in which each gate is encrypted, and an Oblivious Transfer (OT) that is responsible for letting Bob know his encrypted input.
The code implements the maximum of two sets of values. The script can handle integers of at most 6 bits. In this implementation privacy is respected since neither Alice nor Bob can 
understand the set of the other. The same holds for correctness: assuming that both actors always behave honestly, the result obtained through Yao’s protocol is guaranteed to be 
the same as that obtained through a standard computation (this is verified by a program procedure).
