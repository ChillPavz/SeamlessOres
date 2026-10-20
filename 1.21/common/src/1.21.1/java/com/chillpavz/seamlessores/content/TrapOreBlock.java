package com.chillpavz.seamlessores.content;

import com.chillpavz.seamlessores.Constants;
import net.minecraft.core.BlockPos;
import net.minecraft.util.valueproviders.IntProvider;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Explosion;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelAccessor;
import net.minecraft.world.level.block.state.BlockState;

import java.lang.invoke.MethodHandle;
import java.lang.invoke.MethodHandles;
import java.lang.invoke.MethodType;

/**
 * Born in Chaos' infected diamond (its author's permission, 20 Oct 2026): a trap that looks like diamond
 * ore and drops nothing. Breaking it, or blowing it up, runs that mod's own procedure, which spawns a
 * Diamond Thermite. Its variant runs the same two procedures, found by name, so there is no compile-time
 * dependency and the installed version's behaviour is the one that runs. If they cannot be found or a call
 * fails, it logs once and stays a block that drops nothing, as its source does.
 *
 * <p>The source runs the break procedure from a loader-only hook after the block is gone; this runs it from
 * {@code playerWillDestroy}, just before, which every loader has. The procedure only spawns at the position.
 */
public class TrapOreBlock extends HostedOreBlock {

    private static final String PROCEDURES = "net.mcreator.borninchaosv.procedures.";
    private static final MethodType BREAK = MethodType.methodType(void.class, LevelAccessor.class,
            double.class, double.class, double.class, Entity.class);
    private static final MethodType EXPLODE = MethodType.methodType(void.class, LevelAccessor.class,
            double.class, double.class, double.class);

    private static volatile MethodHandle onBreak;
    private static volatile MethodHandle onExplode;
    private static volatile boolean resolved;
    private static volatile boolean failed;

    /** Whether this ore's variants are traps of this kind. */
    public static boolean handles(OreType ore) {
        return "infected_diamond".equals(ore.key());
    }

    public TrapOreBlock(OreVariant variant, IntProvider xp, Properties properties) {
        super(variant, xp, properties);
    }

    @Override
    public BlockState playerWillDestroy(Level level, BlockPos pos, BlockState state, Player player) {
        final BlockState result = super.playerWillDestroy(level, pos, state, player);
        if (!level.isClientSide() && resolve() && onBreak != null) {
            try {
                onBreak.invoke((LevelAccessor) level, (double) pos.getX(), (double) pos.getY(), (double) pos.getZ(),
                        (Entity) player);
            } catch (Throwable e) {
                fail(e);
            }
        }
        return result;
    }

    @Override
    public void wasExploded(Level level, BlockPos pos, Explosion explosion) {
        super.wasExploded(level, pos, explosion);
        if (!level.isClientSide() && resolve() && onExplode != null) {
            try {
                onExplode.invoke((LevelAccessor) level, (double) pos.getX(), (double) pos.getY(), (double) pos.getZ());
            } catch (Throwable e) {
                fail(e);
            }
        }
    }

    private static boolean resolve() {
        if (!resolved) {
            resolved = true;
            try {
                final MethodHandles.Lookup lookup = MethodHandles.publicLookup();
                onBreak = lookup.findStatic(Class.forName(PROCEDURES + "InfectedDiamondOreBrekProcedure"), "execute", BREAK);
                onExplode = lookup.findStatic(Class.forName(PROCEDURES + "DeepslateDiamondOreInsestProcedure"), "execute", EXPLODE);
            } catch (ReflectiveOperationException | LinkageError e) {
                fail(e);
            }
        }
        return !failed;
    }

    private static void fail(Throwable e) {
        if (!failed) {
            failed = true;
            Constants.LOG.warn("Born in Chaos' infected diamond procedures could not be called ({}); its tuff variant "
                    + "now drops nothing and spawns nothing. Everything else is unaffected.", e.toString());
        }
    }
}
