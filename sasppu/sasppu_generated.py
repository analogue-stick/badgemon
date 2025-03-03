#!/bin/python3

with open("sasppu_handle_bg_gen.S", "w") as f:
    idents = []
    for cmath_enable in range(2):
        for sub_win_enable in range(2):
            for main_win_enable in range(2):
                for subwin in range(16):
                    for mainwin in range(16):
                        unique = ("handle_bg_" + 
                                str(cmath_enable) + "_" + 
                                str(sub_win_enable) + "_" +
                                str(main_win_enable) + "_" +
                                str(subwin) + "_" +
                                str(mainwin)) 
                        
                        idents.append(unique)
                        
                        f.write(unique + ":\n")
                        f.write("handle_bg_wrap " + 
                                unique + ", " + 
                                str(cmath_enable) + ", " +
                                str(sub_win_enable) + ", " +
                                str(main_win_enable) + ", " +
                                str(subwin) + ", " +
                                str(mainwin) +
                            "\n")
                        f.write("retw.n\n")
                        
    f.write("handle_bg_lookup:\n")
    for ident in idents:
        f.write(".long " + ident+"\n")