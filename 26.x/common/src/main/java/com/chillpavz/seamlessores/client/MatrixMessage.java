package com.chillpavz.seamlessores.client;

import com.chillpavz.seamlessores.Constants;
import com.chillpavz.seamlessores.SeamlessOresConfig;
import net.minecraft.ChatFormatting;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

/**
 * A short note in chat that Seamless Ores now has ore variants for modded stones (until 4.x the separate
 * Seamless Ores: Matrix). Client only; each loader calls {@link #onClientTick} from its own end-of-tick
 * event.
 *
 * <p>It shows a few seconds after the player enters a world, once on this installation, the first time
 * after updating to the version that merged it (a one-line marker file in the config folder remembers
 * it), unless the config's {@code showUpdateNote} is off. Asking players to remove the old Matrix mod is that mod's own red note, on every world load, so
 * this one never mentions it. Changing {@link #NOTE} makes it show once more to everyone.
 *
 * <p>It goes through {@code LocalPlayer.sendSystemMessage}, which is the same on every 26.x version;
 * the chat component itself moved when 26.2 split {@code Gui} into {@code Gui} and {@code Hud}.
 */
public final class MatrixMessage {

    /** What the marker file holds once the one-time note has been seen. */
    private static final String NOTE = "matrix-merged-1";
    private static final String MARKER = Constants.MOD_ID + "-note.txt";

    /** Three seconds in the world, so the note is not buried under the join messages. */
    private static final int DELAY_TICKS = 60;

    /** Decided once per world joined; reset when the player leaves. */
    private static boolean decided;
    private static int ticksInWorld;

    private MatrixMessage() {
    }

    public static void onClientTick(Minecraft minecraft) {
        try {
            final LocalPlayer player = minecraft.player;
            if (player == null || minecraft.level == null) {
                decided = false;
                ticksInWorld = 0;
                return;
            }
            if (decided || ++ticksInWorld < DELAY_TICKS) {
                return;
            }
            decided = true;
            if (!SeamlessOresConfig.showUpdateNote) {
                return;   // switched off in the config: no note, and no marker written either
            }
            final Path marker = minecraft.gameDirectory.toPath().resolve("config").resolve(MARKER);
            if (NOTE.equals(readMarker(marker))) {
                return;
            }
            player.sendSystemMessage(merged());
            Constants.LOG.info("Showed the Seamless Ores: Matrix merge note in chat (first time on this installation)");
            writeMarker(marker);
        } catch (RuntimeException | LinkageError e) {
            // A chat note is never worth a crash.
            decided = true;
            Constants.LOG.warn("Could not show the Seamless Ores: Matrix note in chat", e);
        }
    }

    private static String readMarker(Path marker) {
        try {
            return Files.isRegularFile(marker) ? Files.readString(marker, StandardCharsets.UTF_8).trim() : null;
        } catch (IOException e) {
            return null;
        }
    }

    private static void writeMarker(Path marker) {
        try {
            Files.createDirectories(marker.getParent());
            Files.writeString(marker, NOTE + "\n", StandardCharsets.UTF_8);
        } catch (IOException e) {
            // Unwritable config folder: the note may show again next time, which is harmless.
            Constants.LOG.warn("Could not save {}, so the Matrix note may show again", marker, e);
        }
    }

    static MutableComponent merged() {
        return Component.literal("[Seamless Ores] ").withStyle(ChatFormatting.GOLD)
                .append(Component.literal("Now with ore variants for modded stones.").withStyle(ChatFormatting.YELLOW))
                .append(Component.literal("\nOres in the stones other mods add match their rock too, with nothing"
                        + " else to install.").withStyle(ChatFormatting.WHITE));
    }
}
