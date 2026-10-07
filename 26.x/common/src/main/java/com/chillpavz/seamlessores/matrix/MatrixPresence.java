package com.chillpavz.seamlessores.matrix;

import com.chillpavz.seamlessores.platform.Services;

/**
 * Whether the retired companion mod, Seamless Ores: Matrix, is still installed next to us.
 *
 * <p>Its ores are part of Seamless Ores now. While it is installed it keeps generating them under its
 * own ids, our copy of its worldgen stands down, and no old id is aliased (an alias may not shadow an
 * id that is still registered). Our blocks stay registered either way: the block set must never
 * depend on another mod's presence beyond the hosts and ores themselves. Never a hard incompatibility.
 */
public final class MatrixPresence {

    public static final String OLD_MOD_ID = "seamlessoresmatrix";

    private MatrixPresence() {}

    public static boolean oldMatrixInstalled() {
        return Services.PLATFORM.isModLoaded(OLD_MOD_ID);
    }
}
