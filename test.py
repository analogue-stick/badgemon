from prototype.game import mons, abilities, moves, constants, battle_main

moves = [moves.Move(
        "Kills you {i}".format(i=i), "Kills you with hammers", constants.MonType.DRAGON, 20, 999, 100,
        moves.MoveEffect.recoil_damage(20).then(
            moves.MoveEffect.apply_status_effect(constants.StatusEffect.BURNED, 0.3)
        )
    ) for i in range(10)]

mon_template = mons.MonTemplate(
    "guy", "fuckin dude", [constants.MonType.FIGHTING, constants.MonType.FIRE],
    abilities.Ability.NO_ABILITY, None, None,
    85, 135, 130, 60, 70, 25, [
        (moves[0], 5),
        (moves[1], 5),
        (moves[2], 8),
        (moves[3], 13),
        (moves[4], 21),
        (moves[5], 30),
        (moves[6], 40)
    ]
)

mon1 = mons.Mon(mon_template, 5).set_nickname("small guy")
mon2 = mons.Mon(mon_template, 17).set_nickname("mr. 17")
mon3 = mons.Mon(mon_template, 17).set_nickname("David")
mon4 = mons.Mon(mon_template, 33).set_nickname("large individual")
mon5 = mons.Mon(mon_template, 100).set_nickname("biggest dude")


battle = battle_main.Battle(mon1, mon2)

print("\n\n".join(
    "\"{}\" (species: {}) LV {} [{} / {} HP]\n{}\nIVs: {}\nEVs: {}\nMoves:\n{}".format(
        mon.nickname, mon.template.name, mon.level, mon.hp, mon.stats[0], ", ".join(
            "{} {}".format(mon.stats[i], constants.stat_names[i]) for i in range(6)
        ), mon.ivs, mon.evs, ", ".join(
            "{} ({}/{} PP)".format(move.name, mon.pp[i], move.max_pp) for i, move in enumerate(mon.moves)
        )
    ) for mon in [mon1, mon2, mon3, mon4, mon5]
))
