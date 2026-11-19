"""Synthetic checks for the chat spike detector. Run: python test_detector.py"""
import random
import sys

sys.path.insert(0, __import__("os").path.dirname(__file__))
import autoclip  # noqa: E402

T0 = 1_800_000_000.0  # aligned to a 10 s boundary


def cfg(**kw):
    c, _ = autoclip.parse_args(["dummy"])
    for k, v in kw.items():
        setattr(c, k, v)
    return c


def run(messages, c):
    det = autoclip.SpikeDetector(c)
    spikes = []
    for t, u, m in sorted(messages):
        spikes += det.tick(t)
        det.add(t, u, m)
    spikes += det.tick(messages[-1][0] + 30)
    return spikes


def poisson_chat(rng, rate_per_s, t_from, t_to, users=400, text="hello"):
    out, t = [], t_from
    while True:
        t += rng.expovariate(rate_per_s)
        if t >= t_to:
            return out
        out.append((t, f"u{rng.randrange(users)}", text))


def test_injected_spikes_found():
    rng = random.Random(1)
    msgs = poisson_chat(rng, 2.0, T0, T0 + 1800)
    events = [T0 + 400, T0 + 900, T0 + 1500]
    for e in events:
        msgs += poisson_chat(rng, 9.0, e, e + 12, users=3000, text="KEKW")
    sp = run(msgs, cfg())
    onsets = [s.onset for s in sp]
    assert len(sp) == 3, f"expected 3 spikes, got {len(sp)} at {[o - T0 for o in onsets]}"
    for e, o in zip(events, onsets):
        assert abs(o - e) <= 3, f"onset {o - T0:.0f} too far from event {e - T0:.0f}"
    print("ok  injected spikes found, onsets within 3 s:", [round(o - e, 1) for e, o in zip(events, onsets)])


def test_flat_noisy_chat_quiet():
    for rate in (0.3, 2.0, 15.0):
        rng = random.Random(int(rate * 10))
        sp = run(poisson_chat(rng, rate, T0, T0 + 3600, users=5000), cfg())
        assert len(sp) <= 1, f"{len(sp)} false spikes in an hour of flat chat at {rate}/s"
        print(f"ok  flat chat at {rate}/s for 1 h -> {len(sp)} false spikes")


def test_sustained_hype_fires_once():
    rng = random.Random(7)
    msgs = poisson_chat(rng, 2.0, T0, T0 + 600)
    msgs += poisson_chat(rng, 10.0, T0 + 300, T0 + 420, users=3000, text="LETS GOOO")
    sp = run(msgs, cfg())
    assert len(sp) == 1, f"sustained 2-minute hype gave {len(sp)} clips"
    print("ok  2 minutes of continuous hype -> 1 clip")


def test_small_chat_floor():
    rng = random.Random(3)
    base = poisson_chat(rng, 0.1, T0, T0 + 900, users=30)
    small = base + [(T0 + 500 + i * 0.5, f"x{i}", "ok") for i in range(4)]
    assert len(run(small, cfg())) == 0, "4 plain messages should not beat the min-score floor"
    big = base + [(T0 + 500 + i * 0.4, f"x{i}", "LMAO") for i in range(14)]
    assert len(run(big, cfg())) == 1, "14 hype messages in a quiet chat should be a spike"
    print("ok  quiet chat: 4-message blip ignored, 14-message burst clipped")


def test_one_spammer_cannot_trigger():
    rng = random.Random(5)
    msgs = poisson_chat(rng, 1.0, T0, T0 + 900)
    msgs += [(T0 + 600 + i * 0.1, "spammer", "KEKW KEKW") for i in range(80)]
    assert len(run(msgs, cfg())) == 0, "one user spamming must not make a clip"
    print("ok  one user sending 80 messages -> no clip")


def test_bots_ignored():
    rng = random.Random(9)
    msgs = poisson_chat(rng, 1.0, T0, T0 + 900)
    msgs += [(T0 + 600 + i * 0.1, b, "!giveaway") for i in range(3) for b in autoclip.BOTS]
    assert len(run(msgs, cfg())) == 0
    print("ok  bot burst ignored")


def test_chat_poll_is_not_a_moment():
    # found live on Lacy: "type ME in chat if you've been up since 5am" made a 7.7x spike of "me"
    rng = random.Random(2)
    base = poisson_chat(rng, 2.0, T0, T0 + 900, text="hello there")
    poll = base + [(T0 + 600 + i * 0.1, f"p{i}", rng.choice(["me", "mee", "ME"])) for i in range(80)]
    flood = base + [(T0 + 600 + i * 0.1, f"p{i}", "KEKW") for i in range(80)]
    assert len(run(poll, cfg())) == 0, "a prompted chat poll must not make a clip"
    assert len(run(flood, cfg())) == 1, "an emote flood is a real reaction and must make a clip"
    print("ok  'type ME in chat' poll ignored, KEKW flood clipped")


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("all detector tests passed")
