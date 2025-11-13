import 'package:flutter/material.dart';
import 'package:table_calendar/table_calendar.dart';

class Event {
  String title;

  Event(this.title);
}

Map<DateTime, List<Event>> events = {
  DateTime.utc(2025, 5, 29): [Event('김치찜')],
  DateTime.utc(2025, 5, 14): [Event('돼지고기 카레')],
};

DateTime focusedDay = DateTime.now();

Widget BuildOutSideDay(
  BuildContext context,
  DateTime date,
  DateTime focusedDay,
) {
  Color dateColor = Colors.grey;

  if (date.weekday == DateTime.saturday) {
    dateColor = Colors.blueGrey;
  } else if (date.weekday == DateTime.sunday) {
    dateColor = Colors.redAccent;
  }

  return Align(
    alignment: Alignment.topCenter,
    child: Text('${date.day}', style: TextStyle(color: dateColor)),
  );
}

Widget BuildDefaultDay(
  BuildContext context,
  DateTime date,
  DateTime focusedDay,
) {
  return Center(
    child: Text(
      '${date.day}',
      style: TextStyle(
        color: isSameDay(date, focusedDay) ? Colors.blue : Colors.black,
      ),
    ),
  );
}

Widget BuildSelectedDay(
  BuildContext context,
  DateTime date,
  DateTime focusedDay,
) {
  return Center(
    child: Text('${date.day}', style: TextStyle(color: Colors.green)),
  );
}

Widget BuildToday(BuildContext context, DateTime date, DateTime focusedDay) {
  return Center(
    child: Text(
      '${date.day}',
      style: TextStyle(color: Colors.blue, fontWeight: FontWeight.bold),
    ),
  );
}

Widget? BuildCookMarker(
  BuildContext context,
  DateTime date,
  List<Event> events,
) {
  if (events.isNotEmpty) {
    List<Event> eventList = events.cast<Event>();
    return Align(
      alignment: Alignment.bottomCenter,
      child: BuildEventText(eventList[0].title, Colors.purpleAccent),
    );
  }
  return null;
}

Widget BuildEventText(String event, Color color) {
  return Text(event, maxLines: 1, style: TextStyle(color: color, fontSize: 10));
}

Widget? BuildDowDay(BuildContext context, DateTime date) {
  if (date.weekday == DateTime.saturday) {
    return const Center(child: Text('토', style: TextStyle(color: Colors.blue)));
  } else if (date.weekday == DateTime.sunday) {
    return const Center(child: Text('일', style: TextStyle(color: Colors.red)));
  }
  return null;
}
