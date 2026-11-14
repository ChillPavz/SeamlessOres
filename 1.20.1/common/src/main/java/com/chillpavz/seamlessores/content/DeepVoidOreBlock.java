package com.chillpavz.seamlessores.content;

import com.chillpavz.seamlessores.Constants;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.tags.TagKey;
import net.minecraft.util.valueproviders.IntProvider;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Explosion;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelAccessor;
import net.minecraft.world.level.LevelReader;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;

import java.lang.invoke.MethodHandle;
import java.lang.invoke.MethodHandles;
import java.lang.invoke.MethodType;

/**
 * The Deep Void's sulfur and voidrium, in tuff: each behaves as its source block does (The Deep Void 1.99.5, read from
 * its bytecode). Sulfur asks that mod's own procedures, found by name, whether it may stay where it is, what to do
 * when a neighbour changes, and what happens when it is blown up (it explodes in turn); it burns at flammability 15.
 * Voidrium can only be harvested with a tool in {@code the_deep_void:can_mine_voidrium}, as its source's harvest
 * condition reads. Experience and strength are the OreType's (the source spawns its experience from a procedure that
 * matches the game's ore rule).
 *
 * <p>Nothing here is a compile-time dependency: the procedures are looked up by name, so the installed version's
 * behaviour is the one that runs. If they cannot be found or a call fails, it logs once and the sulfur variant
 * becomes a plain ore. {@code canHarvestBlock} and {@code getFlammability} are Forge's block methods (The Deep Void is
 * a Forge mod); elsewhere they are ordinary unused methods.
 */
public class DeepVoidOreBlock extends HostedOreBlock {

    private static final String SULFUR = "the_deep_void_sulfur";
    private static final String VOIDRIUM = "the_deep_void_voidrium";
    private static final String PROCEDURES = "net.sombrius.thedeepvoid.procedures.";
    private static final MethodType AT = MethodType.methodType(void.class, LevelAccessor.class,
            double.class, double.class, double.class);
    private static final TagKey<Item> CAN_MINE_VOIDRIUM =
            TagKey.create(Registries.ITEM, new ResourceLocation("the_deep_void", "can_mine_voidrium"));

    private static volatile MethodHandle validPlacement;
    private static volatile MethodHandle neighbourChanged;
    private static volatile MethodHandle exploded;
    private static volatile boolean resolved;
    private static volatile boolean failed;

    private final boolean sulfur;

    /** Whether this ore's variants are of this kind. */
    public static boolean handles(OreType ore) {
        return SULFUR.equals(ore.key()) || VOIDRIUM.equals(ore.key());
    }

    public DeepVoidOreBlock(OreVariant variant, IntProvider xp, Properties properties) {
        super(variant, xp, properties);
        this.sulfur = SULFUR.equals(variant.ore().key());
    }

    // --- Sulfur ------------------------------------------------------------------------------------

    @Override
    public boolean canSurvive(BlockState state, LevelReader level, BlockPos pos) {
        if (sulfur && level instanceof LevelAccessor world && resolve()) {
            try {
                return (boolean) validPlacement.invoke(world, (double) pos.getX(), (double) pos.getY(), (double) pos.getZ());
            } catch (Throwable e) {
                fail(e);
            }
        }
        return super.canSurvive(state, level, pos);
    }

    @Override
    public BlockState updateShape(BlockState state, Direction direction, BlockState neighbour, LevelAccessor level,
                                  BlockPos pos, BlockPos neighbourPos) {
        if (sulfur && !state.canSurvive(level, pos)) {
            return Blocks.AIR.defaultBlockState();
        }
        return super.updateShape(state, direction, neighbour, level, pos, neighbourPos);
    }

    @Override
    public void neighborChanged(BlockState state, Level level, BlockPos pos, Block block, BlockPos from, boolean moving) {
        super.neighborChanged(state, level, pos, block, from, moving);
        call(neighbourChanged, level, pos);
    }

    @Override
    public void wasExploded(Level level, BlockPos pos, Explosion explosion) {
        super.wasExploded(level, pos, explosion);
        call(exploded, level, pos);
    }

    /** Forge: fire consumes it as it does the source. */
    public int getFlammability(BlockState state, BlockGetter level, BlockPos pos, Direction direction) {
        return sulfur ? 15 : 0;
    }

    // --- Voidrium ----------------------------------------------------------------------------------

    /** Forge: only a tool the source accepts harvests it. */
    public boolean canHarvestBlock(BlockState state, BlockGetter level, BlockPos pos, Player player) {
        if (!sulfur) {
            return player.getMainHandItem().is(CAN_MINE_VOIDRIUM);
        }
        return !state.requiresCorrectToolForDrops() || player.hasCorrectToolForDrops(state);
    }

    // --- The procedures ------------------------------------------------------------------------------

    private void call(MethodHandle handle, Level level, BlockPos pos) {
        if (sulfur && !level.isClientSide() && resolve()) {
            try {
                handle.invoke((LevelAccessor) level, (double) pos.getX(), (double) pos.getY(), (double) pos.getZ());
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
                validPlacement = lookup.findStatic(Class.forName(PROCEDURES + "SulfurOreBlockValidPlacementConditionProcedure"),
                        "execute", MethodType.methodType(boolean.class, LevelAccessor.class, double.class, double.class, double.class));
                neighbourChanged = lookup.findStatic(Class.forName(PROCEDURES + "SulfurOreNeighbourBlockChangesProcedure"), "execute", AT);
                exploded = lookup.findStatic(Class.forName(PROCEDURES + "SulfurOreBlockDestroyedByExplosionProcedure"), "execute", AT);
            } catch (ReflectiveOperationException | LinkageError e) {
                fail(e);
            }
        }
        return !failed;
    }

    private static void fail(Throwable e) {
        if (!failed) {
            failed = true;
            Constants.LOG.warn("The Deep Void's sulfur procedures could not be called ({}); its tuff variant is now a "
                    + "plain ore. Everything else is unaffected.", e.toString());
        }
    }
}
