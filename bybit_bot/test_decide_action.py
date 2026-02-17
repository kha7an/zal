"""
Ruchnoj test logiki decide_action bez zaprosov k Bybit.

Zapusk:
  python -m bybit_bot.test_decide_action
"""

from bybit_bot.signals import decide_action


def print_case(title: str, signal_prev: int, signal_now: int, position_side):
    action = decide_action(signal_now, signal_prev, position_side)
    pos_txt = position_side or "net"
    print(f"{title}: prev={signal_prev}, now={signal_now}, pozicija={pos_txt:5} -> action={action}")


def main():
    print("Test decide_action (bez Bybit, tol'ko logika)...\n")

    # Bazovye scenarii:
    # 1) Net pozicii, pridjot novyj Up/Down signal
    print_case("1) Net pozicii, 0 -> 1 (novyj Up)", 0, 1, None)
    print_case("2) Net pozicii, 0 -> -1 (novyj Down)", 0, -1, None)

    # 2) Net pozicii, signal uzhe byl i ostalsja tem zhe (povtornaja D-svecha)
    print_case("3) Net pozicii, 1 -> 1 (prodolzhenie Up)", 1, 1, None)
    print_case("4) Net pozicii, -1 -> -1 (prodolzhenie Down)", -1, -1, None)

    # 3) Uje est' pozicija
    print_case("5) Long, signal 1 (derzhim)", 1, 1, "long")
    print_case("6) Long, signal 0 (zakryt')", 1, 0, "long")
    print_case("7) Long, signal -1 (zakryt')", 1, -1, "long")

    print_case("8) Short, signal -1 (derzhim)", -1, -1, "short")
    print_case("9) Short, signal 0 (zakryt')", -1, 0, "short")
    print_case("10) Short, signal 1 (zakryt')", -1, 1, "short")


if __name__ == "__main__":
    main()

