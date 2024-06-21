#!/usr/bin/env python3
import logging
import ot
import util
import yao
import argparse
from abc import ABC, abstractmethod
from format import read_input, verify_output, write_to_output_file, bin_to_decimal, print_alice_to_bob

logging.basicConfig(format="[%(levelname)s] %(message)s",
                    level=logging.WARNING)


class YaoGarbler(ABC):
    """An abstract class for Yao garblers (e.g. Alice)."""
    def __init__(self, circuits):
        circuits = util.parse_json(circuits)
        self.name = circuits["name"]
        self.circuits = []

        for circuit in circuits["circuits"]:
            garbled_circuit = yao.GarbledCircuit(circuit)
            pbits = garbled_circuit.get_pbits()
            entry = {
                "circuit": circuit,
                "garbled_circuit": garbled_circuit,
                "garbled_tables": garbled_circuit.get_garbled_tables(),
                "keys": garbled_circuit.get_keys(),
                "pbits": pbits,
                "pbits_out": {w: pbits[w]
                              for w in circuit["out"]},
            }
            self.circuits.append(entry)

    @abstractmethod
    def start(self):
        pass


class Alice(YaoGarbler):
    """Alice is the creator of the Yao circuit.

    Alice creates a Yao circuit and sends it to the evaluator along with her
    encrypted inputs.

    Attributes:
        circuits: the JSON file containing the circuit
        oblivious_transfer: Optional; enable the Oblivious Transfer protocol
            (True by default).
    """
    def __init__(self, circuits, oblivious_transfer=True):
        super().__init__(circuits)
        self.socket = util.GarblerSocket()
        self.ot = ot.ObliviousTransfer(self.socket, enabled=oblivious_transfer)
        self.data_alice = read_input('input/Alice.txt')

    def start(self):
        """Start Yao protocol."""
        for circuit in self.circuits:
            to_send = {
                "circuit": circuit["circuit"],
                "garbled_tables": circuit["garbled_tables"],
                "pbits_out": circuit["pbits_out"],
            }
            logging.debug(f"Sending {circuit['circuit']['id']}")
            print(f"Sending {circuit['circuit']['id']}")

            self.socket.send_wait(to_send)
            self.print(circuit)

    def print(self, entry):
        """
        Args:
            entry: A dict representing the circuit to evaluate.
        """
        circuit, pbits, keys = entry["circuit"], entry["pbits"], entry["keys"]
        outputs = circuit["out"]
        a_wires = circuit.get("alice", [])  # Alice's wires
        a_inputs = {}  # map from Alice's wires to (key, encr_bit) inputs
        b_wires = circuit.get("bob", [])  # Bob's wires
        b_keys = {  # map from Bob's wires to a pair (key, encr_bit)
            w: self._get_encr_bits(pbits[w], key0, key1)
            for w, (key0, key1) in keys.items() if w in b_wires
        }


        # Read the numbers from the input file, it performs a max computation and converts the result
        # to bits, which are zero-filled to 6 bits. The bits are then converted to a list
        bits_a = list(f"{max(self.data_alice):b}".zfill(6))
        bits_a = [int(i) for i in bits_a]
        # Map Alice's wires to (key, encr_bit)
        for i, _ in enumerate(a_wires):
            a_inputs[a_wires[i]] = (keys[a_wires[i]][bits_a[i]],
                                    pbits[a_wires[i]] ^ bits_a[i])
        # Send Alice's encrypted inputs and keys to Bob
        print_alice_to_bob(a_inputs, a_wires, b_keys)
        result = self.ot.get_result(a_inputs, b_keys)
        # Write the output informations to the file
        str_result = ''.join([str(result[w]) for w in outputs])
        write_to_output_file(f'Alice\'s input max is {max(self.data_alice)}\n')
        verify_output(bin_to_decimal(str_result))
        print('Computation completed, all the information are in the files.')

    def _get_encr_bits(self, pbit, key0, key1):
        return ((key0, 0 ^ pbit), (key1, 1 ^ pbit))


class Bob:
    """Bob is the receiver and evaluator of the Yao circuit.

    Bob receives the Yao circuit from Alice, computes the results and sends
    them back.

    Args:
        oblivious_transfer: Optional; enable the Oblivious Transfer protocol
            (True by default).
    """
    def __init__(self, oblivious_transfer=True):
        self.socket = util.EvaluatorSocket()
        self.ot = ot.ObliviousTransfer(self.socket, enabled=oblivious_transfer)
        self.data_bob = read_input('input/Bob.txt')

    def listen(self):
        """Start listening for Alice messages."""
        logging.info("Start listening")
        print("Start listening")
        try:
            for entry in self.socket.poll_socket():
                self.socket.send(True)
                self.send_evaluation(entry)
        except KeyboardInterrupt:
            logging.info("Stop listening\n")
            print("Stop listening\n")

    def send_evaluation(self, entry):
        """Evaluate yao circuit and send back the results.

        Args:
            entry: A dict representing the circuit to evaluate.
        """
        circuit, pbits_out = entry["circuit"], entry["pbits_out"]
        garbled_tables = entry["garbled_tables"]
        a_wires = circuit.get("alice", [])  # list of Alice's wires
        b_wires = circuit.get("bob", [])  # list of Bob's wires

        print(f"Received {circuit['id']}")
        bits_b = list(f"{max(self.data_bob):b}".zfill(6))
        bits_b = [int(i) for i in bits_b]
        # Create dict mapping each wire of Bob to Bob's input
        b_inputs_clear = {
            b_wires[i]: bits_b[i]
            for i in range(len(b_wires))
        }
        # Print to screen the circuit received info and write all the info to the output file
        write_to_output_file(clear=True)
        write_to_output_file(f'Bob\'s input max is {max(self.data_bob)}\n')
        # Evaluate and send result to Alice
        self.ot.send_result(circuit, garbled_tables, pbits_out,
                            b_inputs_clear)


class LocalTest(YaoGarbler):
    """A class for local tests.

    Print a circuit evaluation or garbled tables.

    Args:
        circuits: the JSON file containing circuit
        print_mode: Print a clear version of the garbled tables or
            the circuit evaluation (the default).
    """
    def __init__(self, circuits, print_mode="circuit"):
        super().__init__(circuits)
        self._print_mode = print_mode
        self.modes = {
            "circuit": self._print_evaluation,
            "table": self._print_tables,
        }
        logging.info(f"Print mode: {print_mode}")

    def start(self):
        """Start local Yao protocol."""
        for circuit in self.circuits:
            self.modes[self.print_mode](circuit)

    def _print_tables(self, entry):
        """Print garbled tables."""
        entry["garbled_circuit"].print_garbled_tables()

    def _print_evaluation(self, entry):
        """Print circuit evaluation."""
        circuit, pbits, keys = entry["circuit"], entry["pbits"], entry["keys"]
        garbled_tables = entry["garbled_tables"]
        outputs = circuit["out"]
        a_wires = circuit.get("alice", [])  # Alice's wires
        a_inputs = {}  # map from Alice's wires to (key, encr_bit) inputs
        b_wires = circuit.get("bob", [])  # Bob's wires
        b_inputs = {}  # map from Bob's wires to (key, encr_bit) inputs
        pbits_out = {w: pbits[w] for w in outputs}  # p-bits of outputs
        N = len(a_wires) + len(b_wires)

        print(f"======== {circuit['id']} ========")

        # Generate all possible inputs for both Alice and Bob
        for bits in [format(n, 'b').zfill(N) for n in range(2**N)]:
            bits_a = [int(b) for b in bits[:len(a_wires)]]  # Alice's inputs
            bits_b = [int(b) for b in bits[N - len(b_wires):]]  # Bob's inputs

            # Map Alice's wires to (key, encr_bit)
            for i in range(len(a_wires)):
                a_inputs[a_wires[i]] = (keys[a_wires[i]][bits_a[i]],
                                        pbits[a_wires[i]] ^ bits_a[i])

            # Map Bob's wires to (key, encr_bit)
            for i in range(len(b_wires)):
                b_inputs[b_wires[i]] = (keys[b_wires[i]][bits_b[i]],
                                        pbits[b_wires[i]] ^ bits_b[i])

            result = yao.evaluate(circuit, garbled_tables, pbits_out, a_inputs,
                                  b_inputs)

            # Format output
            str_bits_a = ' '.join(bits[:len(a_wires)])
            str_bits_b = ' '.join(bits[len(a_wires):])
            str_result = ' '.join([str(result[w]) for w in outputs])

            print(f"  Alice{a_wires} = {str_bits_a} "
                  f"Bob{b_wires} = {str_bits_b}  "
                  f"Outputs{outputs} = {str_result}")

        print()

    @property
    def print_mode(self):
        return self._print_mode

    @print_mode.setter
    def print_mode(self, print_mode):
        if print_mode not in self.modes:
            logging.error(f"Unknown print mode '{print_mode}', "
                          f"must be in {list(self.modes.keys())}")
            return
        self._print_mode = print_mode


def main(party):

    circuit_path="circuit/max.json"
    oblivious_transfer=True,
    print_mode="circuit",
    logging.getLogger().setLevel(logging.WARNING)

    if party == "alice":
        alice = Alice(circuit_path, oblivious_transfer=oblivious_transfer)
        alice.start()
    elif party == "bob":
        bob = Bob(oblivious_transfer=oblivious_transfer)
        bob.listen()
    elif party == "table":
        local = LocalTest(circuit_path, print_mode='table')
        local.start()
    else:
        logging.error(f"Unknown party '{party}'")


def init():
    """
    It collects the arguments to pass to the main function, which is then called.
    :return: None.
    """
    parser = argparse.ArgumentParser(description="Run Yao protocol.")
    parser.add_argument("party",
                        choices=["alice", "bob", "table"],
                        help="The yao party to run.")
    main(party=parser.parse_args().party)


init()