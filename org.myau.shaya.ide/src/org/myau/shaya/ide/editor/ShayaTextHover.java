package org.myau.shaya.ide.editor;

import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

import org.eclipse.core.resources.IFile;
import org.eclipse.jface.text.BadLocationException;
import org.eclipse.jface.text.IDocument;
import org.eclipse.jface.text.IRegion;
import org.eclipse.jface.text.ITextHover;
import org.eclipse.jface.text.ITextViewer;
import org.eclipse.jface.text.Region;
import org.eclipse.ui.IEditorInput;
import org.eclipse.ui.IFileEditorInput;
import org.myau.shaya.ide.toolchain.ShayaToolchain;

/** Hover: symbol / keyword first; engine line as footer. */
public class ShayaTextHover implements ITextHover {

	private static final Map<String, String> NOTES = new HashMap<>();

	static {
		NOTES.put("алг", "Заголовок алгоритма / программы.");
		NOTES.put("нач", "Начало тела (нач…кон).");
		NOTES.put("кон", "Конец тела / алгоритма.");
		NOTES.put("если", "Ветвление: если … то … иначе … все / кесли.");
		NOTES.put("то", "Тогда-ветка условия.");
		NOTES.put("иначе", "Иначе-ветка (тот же уровень, что тело если).");
		NOTES.put("все", "Конец если / выбора.");
		NOTES.put("кесли", "Конец если (некоторые диалекты).");
		NOTES.put("пока", "Цикл с предусловием.");
		NOTES.put("нц", "Начало цикла (нц…кц).");
		NOTES.put("кц", "Конец цикла.");
		NOTES.put("для", "Счётный цикл.");
		NOTES.put("проц", "Процедура.");
		NOTES.put("функ", "Функция.");
		NOTES.put("модуль", "Модуль / единица компиляции.");
		NOTES.put("вывод", "Вывод на экран / в консоль.");
		NOTES.put("ввод", "Ввод значения.");
		NOTES.put("цел", "Целый тип.");
		NOTES.put("вещ", "Вещественный тип.");
		NOTES.put("лит", "Строковый / литерный тип.");
		NOTES.put("лог", "Логический тип.");
		NOTES.put("истина", "Логическая истина.");
		NOTES.put("ложь", "Логическая ложь.");
		NOTES.put("попытка", "Блок обработки ошибок.");
		NOTES.put("выбор", "Множественный выбор.");
	}

	private final ShayaEditor editor;

	public ShayaTextHover(ShayaEditor editor) {
		this.editor = editor;
	}

	@Override
	public String getHoverInfo(ITextViewer textViewer, IRegion hoverRegion) {
		if (textViewer == null || hoverRegion == null) {
			return null;
		}
		IDocument doc = textViewer.getDocument();
		if (doc == null) {
			return null;
		}
		try {
			String word = doc.get(hoverRegion.getOffset(), hoverRegion.getLength()).trim();
			if (word.isEmpty()) {
				return null;
			}
			String footer = engineLine(fileName());
			String note = NOTES.get(word.toLowerCase(Locale.ROOT));
			if (note != null) {
				return note + "\n\n" + footer;
			}
			ShayaKeywords.Dialect dialect = editor != null ? editor.currentDialect() : ShayaKeywords.Dialect.GENERIC;
			if (ShayaKeywords.isKeyword(word, dialect)) {
				return "Ключевое слово / builtin этого диалекта.\n\n" + footer;
			}
			IFile file = null;
			IEditorInput input = editor != null ? editor.getEditorInput() : null;
			if (input instanceof IFileEditorInput) {
				file = ((IFileEditorInput) input).getFile();
			}
			List<ShayaDeclarations.Hit> hits = ShayaDeclarations.findDeclarations(doc, file, word, false);
			if (!hits.isEmpty()) {
				ShayaDeclarations.Hit h = hits.get(0);
				return h.text + "\nF3 / Ctrl+Click — перейти к объявлению\n\n" + footer;
			}
			return "«" + word + "» — объявление в этом файле не найдено.\n"
					+ "F3 / Find References — поиск по проекту (тот же engine).\n\n" + footer;
		} catch (BadLocationException e) {
			return null;
		}
	}

	@Override
	public IRegion getHoverRegion(ITextViewer textViewer, int offset) {
		IDocument doc = textViewer.getDocument();
		if (doc == null) {
			return null;
		}
		try {
			int start = offset;
			while (start > 0 && ShayaIdentifiers.isIdentPart(doc.getChar(start - 1))) {
				start--;
			}
			int end = offset;
			int len = doc.getLength();
			while (end < len && ShayaIdentifiers.isIdentPart(doc.getChar(end))) {
				end++;
			}
			if (end <= start) {
				return null;
			}
			return new Region(start, end - start);
		} catch (BadLocationException e) {
			return null;
		}
	}

	private String fileName() {
		if (editor == null) {
			return "";
		}
		IEditorInput input = editor.getEditorInput();
		if (input instanceof IFileEditorInput) {
			return ((IFileEditorInput) input).getFile().getName();
		}
		return input != null && input.getName() != null ? input.getName() : "";
	}

	private static String engineLine(String name) {
		String eng = ShayaToolchain.engineIdForName(name);
		if (eng == null) {
			return "ALG · unknown extension";
		}
		return "ALG · " + ShayaToolchain.engineDisplayName(eng) + " · " + name;
	}
}
