from game import mons, abilities, moves, constants, battle_main, calculation, items, player

mon_template = mons.mons_list[0]
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

battle.push_news_entry("hello", "chat", 123)
