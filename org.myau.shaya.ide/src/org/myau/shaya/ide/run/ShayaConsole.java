package org.myau.shaya.ide.run;

import java.nio.charset.StandardCharsets;
import java.util.regex.Pattern;

import org.eclipse.ui.console.ConsolePlugin;
import org.eclipse.ui.console.IConsole;
import org.eclipse.ui.console.IConsoleManager;
import org.eclipse.ui.console.IOConsole;
import org.eclipse.ui.console.IOConsoleOutputStream;
import org.eclipse.ui.console.IPatternMatchListener;
import org.eclipse.ui.console.PatternMatchEvent;
import org.eclipse.ui.console.TextConsole;

public final class ShayaConsole {

	private static final String NAME = "ALG";

	private ShayaConsole() {
	}

	public static IOConsole getConsole() {
		IConsoleManager manager = ConsolePlugin.getDefault().getConsoleManager();
		for (IConsole c : manager.getConsoles()) {
			if (NAME.equals(c.getName()) && c instanceof IOConsole) {
				IOConsole console = (IOConsole) c;
				ensureHyperlinks(console);
				manager.showConsoleView(console);
				return console;
			}
		}
		IOConsole console = new IOConsole(NAME, null);
		ensureHyperlinks(console);
		manager.addConsoles(new IConsole[] { console });
		manager.showConsoleView(console);
		return console;
	}

	private static void ensureHyperlinks(IOConsole console) {
		Object flag = console.getAttribute("shaya.hyperlinks.v3");
		if (Boolean.TRUE.equals(flag)) {
			return;
		}
		addListener(console, ShayaConsoleHyperlinkMatcher.REGEX, false);
		addListener(console, ShayaConsoleHyperlinkMatcher.LINE_REGEX, true);
		console.setAttribute("shaya.hyperlinks.v3", Boolean.TRUE);
	}

	private static void addListener(IOConsole console, String pattern, boolean lineOnly) {
		console.addPatternMatchListener(new IPatternMatchListener() {
			private final ShayaConsoleHyperlinkMatcher delegate = new ShayaConsoleHyperlinkMatcher(lineOnly);

			@Override
			public void connect(TextConsole console) {
				delegate.connect(console);
			}

			@Override
			public void disconnect() {
				delegate.disconnect();
			}

			@Override
			public void matchFound(PatternMatchEvent event) {
				delegate.matchFound(event);
			}

			@Override
			public String getPattern() {
				return pattern;
			}

			@Override
			public int getCompilerFlags() {
				return Pattern.CASE_INSENSITIVE;
			}

			@Override
			public String getLineQualifier() {
				return null;
			}
		});
	}

	public static void showError(String message) {
		IOConsole console = getConsole();
		try {
			IOConsoleOutputStream err = console.newOutputStream();
			err.setEncoding(StandardCharsets.UTF_8.name());
			err.write((message + "\n").getBytes(StandardCharsets.UTF_8));
			err.flush();
		} catch (Exception ignored) {
		}
	}
}
