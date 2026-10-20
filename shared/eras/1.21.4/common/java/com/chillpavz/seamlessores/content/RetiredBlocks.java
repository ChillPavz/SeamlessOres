package com.chillpavz.seamlessores.content;

import com.chillpavz.seamlessores.Constants;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import net.minecraft.core.BlockPos;
import net.minecraft.core.SectionPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.chunk.ChunkAccess;
import net.minecraft.world.level.chunk.LevelChunk;
import net.minecraft.world.level.chunk.LevelChunkSection;
import net.minecraft.world.level.storage.loot.LootParams;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.function.BiConsumer;
import java.util.function.Function;

/**
 * Block ids an earlier release registered and this one no longer builds: the ores the geology rule takes
 * out of the game's own rock. A block id that vanishes from the registry turns every placed block into air
 * and every item into nothing, so each keeps a PLACEHOLDER under its old id, which becomes its host stone:
 * <ul>
 *   <li>placed blocks, when their chunk loads ({@link #convertChunk}, run by each loader's chunk event);</li>
 *   <li>a placeholder placed by hand, at once;</li>
 *   <li>a placeholder item in a player's inventory, on its next tick.</li>
 * </ul>
 * Until then it is drawn, named and dropped as the stone. Never generated and never in a creative tab.
 * Registered exactly where the earlier release registered the variant: its stone present and the ore's
 * mod installed, so a client and a server agree. The list is data (seamlessores/retired_ids.json, from
 * tools/retired_ids.json), and a line is never removed from it.
 */
public final class RetiredBlocks {

    private RetiredBlocks() {}

    private static final String LIST = "/seamlessores/retired_ids.json";

    /** Placeholder block -> its host stone. */
    private static final Map<Block, HostStone> HOSTS = new IdentityHashMap<>();

    private static final List<Placeholder> PLACEHOLDERS = new ArrayList<>();

    private static final AtomicBoolean CONVERTED = new AtomicBoolean();

    private record Placeholder(ResourceLocation id, HostStone host) {}

    /** The list this jar ships, filtered to what the installed mods make present. */
    private static List<Placeholder> present() {
        final List<Placeholder> out = new ArrayList<>();
        try (InputStream in = RetiredBlocks.class.getResourceAsStream(LIST)) {
            if (in == null) {
                return out;
            }
            final JsonObject root = JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8)).getAsJsonObject();
            for (JsonElement element : root.getAsJsonArray("retired")) {
                final JsonObject row = element.getAsJsonObject();
                final HostStone host = HostStone.ALL.stream()
                        .filter(h -> h.name().equals(row.get("host").getAsString())).findFirst().orElse(null);
                final OreType ore = OreType.byKey(row.get("ore").getAsString());
                if (host != null && ore != null && host.present() && ore.isLoaded()) {
                    out.add(new Placeholder(ResourceLocation.fromNamespaceAndPath(Constants.MOD_ID, row.get("id").getAsString()), host));
                }
            }
        } catch (Exception e) {
            Constants.LOG.error("Could not read the retired block ids; old blocks with those ids will be lost", e);
        }
        return out;
    }

    /** Registers the placeholders, after our own blocks. Each is built and registered in one step (setId). */
    public static void registerBlocks(BiConsumer<ResourceLocation, Block> sink) {
        for (Placeholder placeholder : present()) {
            final Block block = new RetiredBlock(placeholder.host(), BlockBehaviour.Properties.of()
                    .strength(1.5F, 6.0F).sound(SoundType.STONE).mapColor(placeholder.host().mapColor())
                    .setId(ResourceKey.create(Registries.BLOCK, placeholder.id())));
            HOSTS.put(block, placeholder.host());
            PLACEHOLDERS.add(placeholder);
            sink.accept(placeholder.id(), block);
        }
        if (!PLACEHOLDERS.isEmpty()) {
            Constants.LOG.info("Registered {} retired block ids as placeholders that become their stone", PLACEHOLDERS.size());
        }
    }

    /** Their items, after {@link #registerBlocks}. */
    public static void registerItems(BiConsumer<ResourceLocation, Item> sink, Function<ResourceLocation, Block> blockById) {
        for (Placeholder placeholder : PLACEHOLDERS) {
            sink.accept(placeholder.id(), new RetiredItem(blockById.apply(placeholder.id()), placeholder.host(),
                    new Item.Properties().useBlockDescriptionPrefix()
                            .setId(ResourceKey.create(Registries.ITEM, placeholder.id()))));
        }
    }

    /**
     * A chunk has loaded: every placeholder in it becomes its stone. Only a chunk that is fully loaded
     * (the load event also fires for chunks still generating, which never hold one), and only sections
     * whose palette holds one, are read. Written into the chunk itself and sent to the clients that see
     * it, never through {@code level.setBlock}: that looks the chunk up, and during spawn preparation the
     * lookup waits on the very load that queued this, which hangs the server.
     */
    public static void convertChunk(ServerLevel level, ChunkAccess chunk) {
        if (HOSTS.isEmpty() || !(chunk instanceof LevelChunk loaded)) {
            return;
        }
        final LevelChunkSection[] sections = chunk.getSections();
        final BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
        int count = 0;
        for (int i = 0; i < sections.length; i++) {
            final LevelChunkSection section = sections[i];
            if (section.hasOnlyAir() || !section.getStates().maybeHas(state -> HOSTS.containsKey(state.getBlock()))) {
                continue;
            }
            final int minY = SectionPos.sectionToBlockCoord(chunk.getSectionYFromSectionIndex(i));
            for (int y = 0; y < 16; y++) {
                for (int z = 0; z < 16; z++) {
                    for (int x = 0; x < 16; x++) {
                        final HostStone host = HOSTS.get(section.getBlockState(x, y, z).getBlock());
                        if (host != null && host.block() != null) {
                            pos.set(chunk.getPos().getMinBlockX() + x, minY + y, chunk.getPos().getMinBlockZ() + z);
                            loaded.setBlockState(pos, host.block().defaultBlockState(), false);
                            level.getChunkSource().blockChanged(pos);
                            count++;
                        }
                    }
                }
            }
        }
        if (count > 0 && CONVERTED.compareAndSet(false, true)) {
            Constants.LOG.info("Retired blocks: {} turned into their stone in chunk {} (logged once)", count, chunk.getPos());
        }
    }

    /** The placeholder block: drawn, named and dropped as its stone, which it becomes when placed. */
    private static final class RetiredBlock extends Block {

        private final HostStone host;

        RetiredBlock(HostStone host, BlockBehaviour.Properties properties) {
            super(properties);
            this.host = host;
        }

        @Override
        public MutableComponent getName() {
            return host.block() != null ? host.block().getName() : super.getName();
        }

        @Override
        protected void onPlace(BlockState state, Level level, BlockPos pos, BlockState old, boolean moved) {
            if (!level.isClientSide() && host.block() != null) {
                level.setBlock(pos, host.block().defaultBlockState(), Block.UPDATE_ALL);
            }
        }

        @Override
        protected List<ItemStack> getDrops(BlockState state, LootParams.Builder params) {
            return host.block() != null ? List.of(new ItemStack(host.block())) : List.of();
        }
    }

    /** The placeholder item: named as its stone, and becomes it in a player's inventory. */
    private static final class RetiredItem extends BlockItem {

        private final HostStone host;

        RetiredItem(Block block, HostStone host, Item.Properties properties) {
            super(block, properties);
            this.host = host;
        }

        @Override
        public Component getName(ItemStack stack) {
            return host.block() != null ? host.block().getName() : super.getName(stack);
        }

        @Override
        public void inventoryTick(ItemStack stack, Level level, Entity entity, int slot, boolean selected) {
            if (level.isClientSide() || !(entity instanceof Player player) || host.block() == null) {
                return;
            }
            final Inventory inventory = player.getInventory();
            for (int i = 0; i < inventory.getContainerSize(); i++) {
                if (inventory.getItem(i) == stack) {
                    inventory.setItem(i, new ItemStack(host.block(), stack.getCount()));
                    return;
                }
            }
        }
    }
}
