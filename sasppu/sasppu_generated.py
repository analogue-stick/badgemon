#!/bin/python3

def generate_window_jump_table(f):
    idents = []
    f.write(".align 4\n")
    for subwin in range(16):
        for mainwin in range(16):
            unique = ("handle_window_" +
                    str(subwin) + "_" +
                    str(mainwin)) 
            
            idents.append(unique)
            
            f.write(unique + ":\n")
            f.write("window_wrapper " +
                    str(subwin) + ", " +
                    str(mainwin) +
                "\n")
                        
    f.write(".align 4\n")
    f.write("window_jump_table:\n")
    for ident in idents:
        f.write(".long " + ident+"\n")

def generate_sprite_jump_table(f):
    idents = []
    f.write(".align 4\n")
    for double in range(2):
        for c_math in range(2):
            for flip_y in range(2):
                for flip_x in range(2):
                    unique = ("handle_sprite_" +
                            str(double) + "_" +
                            str(c_math) + "_" +
                            str(flip_y) + "_" +
                            str(flip_x)) 

                    idents.append(unique)

                    f.write(unique + ":\n")
                    f.write("handle_sprite " + 
                            unique + ", " +
                            str(double) + ", " +
                            str(c_math) + ", " +
                            str(flip_y) + ", " +
                            str(flip_x) + 
                        "\n")
                        
    f.write(".align 4\n")
    f.write("sprite_jump_table:\n")
    for ident in idents:
        f.write(".long " + ident+"\n")

def generate_cmath_jump_table(f):
    idents = []
    f.write(".align 4\n")
    for cmath_enable in range(2):
        for fade_enable in range(2):
            for sub_ss in range(2):
                for add_ss in range(2):
                    for ss_double in range(2):
                        for ss_half in range(2):
                            for ms_double in range(2):
                                for ms_half in range(2):
                                    unique = ("handle_cmath_" +
                                            str(cmath_enable) + "_" +
                                            str(fade_enable) + "_" +
                                            str(sub_ss) + "_" +
                                            str(add_ss) + "_" +
                                            str(ss_double) + "_" +
                                            str(ss_half) + "_" +
                                            str(ms_double) + "_" +
                                            str(ms_half)) 

                                    idents.append(unique)

                                    f.write(unique + ":\n")
                                    f.write("handle_cmath_wrapper " + 
                                            unique + ", " +
                                            str(cmath_enable) + ", " +
                                            str(fade_enable) + ", " +
                                            str(sub_ss) + ", " +
                                            str(add_ss) + ", " +
                                            str(ss_double) + ", " +
                                            str(ss_half) + ", " +
                                            str(ms_double) + ", " +
                                            str(ms_half) +
                                        "\n")
                        
    f.write(".align 4\n")
    f.write("cmath_jump_table:\n")
    for ident in idents:
        f.write(".long " + ident+"\n")

def generate_per_pixel_jump_table(f):
    idents = []
    f.write(".align 4\n")
    for cmath_enable in range(2):
        for bg1_enable in range(2):
            for bg0_enable in range(2):
                for spr1_enable in range(2):
                    for spr0_enable in range(2):
                        unique = ("per_pixel_" +
                                str(cmath_enable) + "_" +
                                str(bg1_enable) + "_" +
                                str(bg0_enable) + "_" +
                                str(spr1_enable) + "_" +
                                str(spr0_enable))

                        idents.append(unique)

                        f.write(unique + ":\n")
                        f.write("per_pixel_macro " + 
                                unique + ", " +
                                str(cmath_enable) + ", " +
                                str(bg1_enable) + ", " +
                                str(bg0_enable) + ", " +
                                str(spr1_enable) + ", " +
                                str(spr0_enable) +
                            "\n")
                        
    f.write(".align 4\n")
    f.write("per_pixel_jump_table:\n")
    for ident in idents:
        f.write(".long " + ident+"\n")

with open("sasppu_gen.S", "w") as f:
    generate_window_jump_table(f)
    generate_sprite_jump_table(f)
    generate_cmath_jump_table(f)
    generate_per_pixel_jump_table(f)
