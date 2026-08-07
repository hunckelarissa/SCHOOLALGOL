package org.myau.shaya.ide.wizards;

/**
 * Hello skeletons for SCHOOLALGOL (.alg) — RU and EN.
 */
public final class ShayaHelloBodies {

	public static final class Spec {
		public final String label;
		public final String ext;
		public final String engine;
		public final String body;
		/** Suggested file stem when creating a sample (e.g. Hello / Hello_en). */
		public final String defaultStem;

		public Spec(String label, String ext, String engine, String body) {
			this(label, ext, engine, body, "Hello");
		}

		public Spec(String label, String ext, String engine, String body, String defaultStem) {
			this.label = label;
			this.ext = ext;
			this.engine = engine;
			this.body = body;
			this.defaultStem = defaultStem;
		}

		@Override
		public String toString() {
			return label + "  (*." + ext + " → " + engine + ")";
		}
	}

	private ShayaHelloBodies() {
	}

	public static Spec[] all() {
		return new Spec[] {
				new Spec("SCHOOLALGOL (RU)", "alg", "SCHOOLALGOL",
						"алг основнаяпрограмма\nнач\n  вывод \"Hello from ALG / SCHOOLALGOL\"\nкон\n",
						"Hello"),
				new Spec("SCHOOLALGOL (EN)", "alg", "SCHOOLALGOL",
						"proc mainprogram\nbegin\n  output \"Hello from ALG / SCHOOLALGOL\"\nend\n",
						"Hello_en"),
		};
	}

	/** Default set created in a new ALG project (RU + EN samples). */
	public static Spec[] projectDefaults() {
		return all();
	}
}
