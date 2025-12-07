import bearcat

ub = bearcat.get_scanner()
ub.get_model()

ub.clear_all()

with open("ch.txt", "r") as f:
    for line in f:
        try:
            ch, freq = line.split(":")
        except ValueError:
            print(f"ignoring line: {line}")
            continue
        c = bearcat.ChannelInfo(int(ch), float(freq))
        ub.set_channel(c)

ub.exit_program_mode()
