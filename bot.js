const TelegramBot = require("node-telegram-bot-api");
const fs = require("fs");
const express = require("express");
const {
  welcomeMessage,
  textAnswers,
  scheduleAnswers,
  holidays,
  imageAnswers,
  allHolidaysKeywords,
  botName,
  greetingKeywords,
  privateWelcomeMessage,
  menu,
} = require("./config");

// ============================================
// التوكن يُقرأ من متغير بيئة BOT_TOKEN (تحطينه بلوحة تحكم Render، مو بالكود)
// ============================================
const TOKEN = process.env.BOT_TOKEN;

if (!TOKEN) {
  console.error("⚠️  ما فيه توكن! تأكدي إنك حاطة BOT_TOKEN بمتغيرات البيئة (Environment Variables).");
  process.exit(1);
}

const bot = new TelegramBot(TOKEN, { polling: true });

// ============================================
// سيرفر بسيط بس عشان Render يعتبر الخدمة "شغالة" (Web Service محتاج يستقبل طلبات)
// خدمة UptimeRobot المجانية بترسل بينج هنا كل شوي عشان يضل صاحي وما ينام
// ============================================
const app = express();
app.get("/", (req, res) => res.send("البوت شغال ✅"));
app.listen(process.env.PORT || 3000, () => {
  console.log("🌐 سيرفر البينج شغال");
});

// ============================================
// مطابقة "تقريبية" (Fuzzy) — تتساهل مع الأخطاء الإملائية والصيغ العامية القريبة
// بدل ما تحتاج الكلمة بالحرف بالحرف
// ============================================

// توحيد شكل الكلمة (همزات، تاء مربوطة، تشكيل)
function normalizeWord(w) {
  return w
    .replace(/[إأآا]/g, "ا")
    .replace(/[ىي]/g, "ي")
    .replace(/ة/g, "ه")
    .replace(/[\u064B-\u0652]/g, "")
    .toLowerCase();
}

// تقسيم الجملة لكلمات منفصلة (بعد تطبيع كل وحدة)
function tokenize(text) {
  return text
    .toString()
    .trim()
    .split(/\s+/)
    .map(normalizeWord)
    .filter(Boolean);
}

// حساب "مسافة التعديل" بين كلمتين (كم حرف لازم تتغير عشان توحدين بينهم)
function levenshtein(a, b) {
  const dp = Array.from({ length: a.length + 1 }, () => new Array(b.length + 1).fill(0));
  for (let i = 0; i <= a.length; i++) dp[i][0] = i;
  for (let j = 0; j <= b.length; j++) dp[0][j] = j;
  for (let i = 1; i <= a.length; i++) {
    for (let j = 1; j <= b.length; j++) {
      dp[i][j] =
        a[i - 1] === b[j - 1]
          ? dp[i - 1][j - 1]
          : 1 + Math.min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1]);
    }
  }
  return dp[a.length][b.length];
}

// هل كلمتين "قريبتين من بعض" بحيث نعتبرهم نفس الكلمة (يسمح بغلطة إملائية بسيطة، وبفرق "ال" التعريف)؟
function withAndWithoutAl(w) {
  // نرجع الكلمة بشكلها الأصلي + بدون "ال" أول الكلمة (لو موجودة) عشان "الثاني" تتطابق مع "ثاني"
  const forms = [w];
  if (w.startsWith("ال") && w.length > 3) forms.push(w.slice(2));
  return forms;
}

function wordsMatch(inputWord, keywordWord) {
  const threshold = keywordWord.length <= 3 ? 0 : keywordWord.length <= 6 ? 1 : 2;
  for (const a of withAndWithoutAl(inputWord)) {
    for (const b of withAndWithoutAl(keywordWord)) {
      if (a === b) return true;
      if (levenshtein(a, b) <= threshold) return true;
    }
  }
  return false;
}

function findMatch(userText) {
  const inputTokens = tokenize(userText);
  let bestEntry = null;
  let bestScore = 0;

  for (const entry of allEntries) {
    for (const kw of entry.keywords) {
      const kwTokens = tokenize(kw);
      // لازم كل كلمة بالأمر تلقى تطابق قريب بالرسالة (مو شرط بنفس الترتيب)
      const allFound = kwTokens.every((kt) => inputTokens.some((it) => wordsMatch(it, kt)));
      if (allFound) {
        const score = kwTokens.reduce((sum, t) => sum + t.length, 0);
        // نفضّل الأمر الأدق (اللي كلماته المفتاحية أطول/أكثر تحديداً)
        if (score > bestScore) {
          bestScore = score;
          bestEntry = entry;
        }
      }
    }
  }
  return bestEntry;
}

// هل الرسالة كلمة ترحيب (السلام عليكم، اهلا، مرحبا...)؟ نفس منطق الفهم التقريبي فوق
function findGreeting(userText) {
  const inputTokens = tokenize(userText);
  for (const kw of greetingKeywords) {
    const kwTokens = tokenize(kw);
    const allFound = kwTokens.every((kt) => inputTokens.some((it) => wordsMatch(it, kt)));
    if (allFound) return true;
  }
  return false;
}

// دمج كل الأسئلة (نصية + صور جداول + صور معلومات + إجازات + كل الإجازات مرة وحدة) بقائمة وحدة للبحث فيها
const allEntries = [
  ...textAnswers.map((item) => ({ ...item, type: "text" })),
  ...scheduleAnswers.map((item) => ({ ...item, type: "image" })),
  ...imageAnswers.map((item) => ({ ...item, type: "image" })),
  ...holidays.map((item) => ({ ...item, type: "holiday" })),
  { keywords: allHolidaysKeywords, type: "allHolidays" },
];

// ============================================
// حساب حالة الإجازة (قبلها / فيها / خلصت) بناءً على تاريخ اللحظة الحالية
// ============================================
function formatDate(date) {
  return `${date.getDate()}/${date.getMonth() + 1}/${date.getFullYear()}`;
}

function daysBetween(a, b) {
  const MS_PER_DAY = 1000 * 60 * 60 * 24;
  // نتجاهل فرق الساعات ونقارن على مستوى اليوم فقط
  const utcA = Date.UTC(a.getFullYear(), a.getMonth(), a.getDate());
  const utcB = Date.UTC(b.getFullYear(), b.getMonth(), b.getDate());
  return Math.round((utcB - utcA) / MS_PER_DAY);
}

function getHolidayReply(holiday) {
  const now = new Date();
  const start = new Date(holiday.start);
  const end = holiday.end ? new Date(holiday.end) : null;

  // الحالة ١: إحنا داخل الإجازة الحين (ولها تاريخ نهاية معروف)
  if (end && now >= start && now <= end) {
    const daysLeft = daysBetween(now, end);
    return `إحنا الآن في ${holiday.name} 🌴\nمتبقي على نهايتها: ${daysLeft} يوم`;
  }

  // الحالة ٢: بدأت الإجازة وما لها تاريخ نهاية معروف (مثل إجازة الصيف)
  if (!end && now >= start) {
    return `إحنا الآن في ${holiday.name} 🌴`;
  }

  // الحالة ٣: الإجازة لسا ما وصلت
  if (now < start) {
    const daysLeft = daysBetween(now, start);
    return `متبقي على ${holiday.name}: ${daysLeft} يوم\n(تبدأ بتاريخ ${formatDate(start)})`;
  }

  // الحالة ٤: الإجازة خلصت من زمان
  return `${holiday.name} كانت من ${formatDate(start)} إلى ${formatDate(end)} وخلصت`;
}

// ============================================
// الترحيب بالأعضاء الجدد (يشتغل بس لو البوت داخل قروب)
// ============================================
bot.on("new_chat_members", (msg) => {
  msg.new_chat_members.forEach((member) => {
    const name = member.first_name || member.username || "عضو جديد";
    bot.sendMessage(msg.chat.id, welcomeMessage(name));
  });
});

// ============================================
// بناء أزرار القائمة الرئيسية (كل قسم بزر لحاله)
// ============================================
function buildMainMenuKeyboard() {
  return {
    inline_keyboard: menu.map((cat) => [{ text: cat.label, callback_data: `cat:${cat.id}` }]),
  };
}

// بناء أزرار قسم فرعي (كل عنصر بزر + زر رجوع تحت)
function buildSubMenuKeyboard(cat) {
  const buttons = cat.items.map((item) => [{ text: item.label, callback_data: `item:${cat.id}:${item.id}` }]);
  buttons.push([{ text: "🔙 رجوع للقائمة الرئيسية", callback_data: "cat:main" }]);
  return { inline_keyboard: buttons };
}

// إرسال محتوى عنصر معين من القائمة (نص/صورة/صور/إجازة/كل الإجازات)
function sendMenuItem(chatId, item) {
  if (item.type === "text") {
    bot.sendMessage(chatId, item.answer);
  } else if (item.type === "holidayIndex") {
    const holiday = holidays[item.holidayIndex];
    bot.sendMessage(chatId, getHolidayReply(holiday));
  } else if (item.type === "allHolidays") {
    const fullList = holidays.map((h) => getHolidayReply(h)).join("\n\n");
    bot.sendMessage(chatId, fullList);
  } else if (item.type === "image") {
    if (!fs.existsSync(item.image)) {
      console.error(`⚠️  الصورة غير موجودة: ${item.image}`);
      return;
    }
    bot.sendPhoto(chatId, item.image, { caption: item.label });
  } else if (item.type === "images") {
    item.images.forEach((img) => {
      if (!fs.existsSync(img.path)) {
        console.error(`⚠️  الصورة غير موجودة: ${img.path}`);
        return;
      }
      bot.sendPhoto(chatId, img.path, { caption: img.label });
    });
  }
}

// ============================================
// الترحيب الشخصي + القائمة الرئيسية (يشتغل بالخاص مع البوت)
// ============================================
function sendWelcomeMenu(chatId, firstName) {
  const name = firstName || "ولي الأمر";
  bot.sendMessage(chatId, privateWelcomeMessage(name), {
    reply_markup: buildMainMenuKeyboard(),
  });
}

// أمر /start (أول رسالة لما حد يفتح البوت لأول مرة)
bot.onText(/^\/start/, (msg) => {
  sendWelcomeMenu(msg.chat.id, msg.from.first_name);
});

// ============================================
// الضغط على الأزرار (القوائم والقوائم الفرعية والعناصر)
// ============================================
bot.on("callback_query", (query) => {
  const chatId = query.message.chat.id;
  const data = query.data;
  bot.answerCallbackQuery(query.id).catch(() => {});

  if (data === "cat:main") {
    bot.sendMessage(chatId, "اختاري القسم اللي تبينه 👇", { reply_markup: buildMainMenuKeyboard() });
    return;
  }

  if (data.startsWith("cat:")) {
    const catId = data.slice(4);
    const cat = menu.find((c) => c.id === catId);
    if (!cat) return;
    bot.sendMessage(chatId, `${cat.label}\nاختاري اللي تبينه 👇`, { reply_markup: buildSubMenuKeyboard(cat) });
    return;
  }

  if (data.startsWith("item:")) {
    const [, catId, itemId] = data.split(":");
    const cat = menu.find((c) => c.id === catId);
    const item = cat && cat.items.find((i) => i.id === itemId);
    if (!item) return;
    sendMenuItem(chatId, item);
    return;
  }
});

// ============================================
// الرد على الرسائل المكتوبة
// ============================================
bot.on("message", (msg) => {
  if (!msg.text) return; // تجاهل الصور/الملفات المرسلة من الأعضاء
  if (msg.text.startsWith("/")) return; // الأوامر زي /start ليها معالج خاص فوق

  // لو الرسالة سلام/ترحيب: نرحب بالاسم ونطلع القائمة الرئيسية
  const greetingMatch = findGreeting(msg.text);
  if (greetingMatch) {
    sendWelcomeMenu(msg.chat.id, msg.from.first_name);
    return;
  }

  const match = findMatch(msg.text);
  if (!match) return; // ما فيه تطابق، البوت ما يرد (عشان ما يزعج المحادثة)

  if (match.type === "text") {
    bot.sendMessage(msg.chat.id, match.answer, { reply_to_message_id: msg.message_id });
  } else if (match.type === "holiday") {
    bot.sendMessage(msg.chat.id, getHolidayReply(match), { reply_to_message_id: msg.message_id });
  } else if (match.type === "allHolidays") {
    const fullList = holidays.map((h) => getHolidayReply(h)).join("\n\n");
    bot.sendMessage(msg.chat.id, fullList, { reply_to_message_id: msg.message_id });
  } else if (match.type === "image") {
    if (match.images) {
      // أمر يرسل أكثر من صورة (زي توزيع الأسابيع: الفصل الأول + الثاني)
      match.images.forEach((img) => {
        if (!fs.existsSync(img.path)) {
          console.error(`⚠️  الصورة غير موجودة: ${img.path}`);
          return;
        }
        bot.sendPhoto(msg.chat.id, img.path, { caption: img.label });
      });
    } else {
      if (!fs.existsSync(match.image)) {
        console.error(`⚠️  الصورة غير موجودة: ${match.image}`);
        return;
      }
      bot.sendPhoto(msg.chat.id, match.image, {
        caption: match.label,
        reply_to_message_id: msg.message_id,
      });
    }
  }
});

console.log(`✅ البوت (${botName}) شغال الحين...`);
