import 'package:flutter/material.dart';
import 'package:table_calendar/table_calendar.dart';
import 'package:cookduck/mypages/cal_event.dart';

class CookCalendar extends StatefulWidget {
  const CookCalendar({super.key});

  @override
  State<CookCalendar> createState() => _CookCalendarState();
}

class _CookCalendarState extends State<CookCalendar> {
  late DateTime selectedDay;
  late DateTime _focusedDay;

  @override
  void initState() {
    super.initState();
    selectedDay = DateTime.now();
    _focusedDay = DateTime.now();
  }

  List<Event> _getEventsForDay(DateTime day) {
    final normalizedDay = DateTime(day.year, day.month, day.day);
    return events[normalizedDay] ?? [];
  }

  @override
  Widget build(BuildContext context) {
    return TableCalendar(
      locale: 'ko_KR',
      focusedDay: _focusedDay,
      firstDay: DateTime.utc(
        focusedDay.year,
        focusedDay.month - 3,
        focusedDay.day,
      ),
      lastDay: DateTime.utc(
        focusedDay.year,
        focusedDay.month + 3,
        focusedDay.day,
      ),
      eventLoader: _getEventsForDay,

      selectedDayPredicate: (day) => isSameDay(selectedDay, day),

      onDaySelected: (DateTime selectedDay, DateTime focusedDay) {
        if (!isSameDay(this.selectedDay, selectedDay)) {
          setState(() {
            this.selectedDay = selectedDay;
            _focusedDay = focusedDay;
          });
        }
      },

      calendarBuilders: CalendarBuilders(
        dowBuilder: BuildDowDay,
        outsideBuilder: BuildOutSideDay,
        defaultBuilder: BuildDefaultDay,
        selectedBuilder: BuildSelectedDay,
        todayBuilder: BuildToday,
        markerBuilder: BuildCookMarker,
      ),
      headerStyle: HeaderStyle(titleCentered: true, formatButtonVisible: false),
      calendarStyle: CalendarStyle(
        canMarkersOverflow: false,
        markerSize: 10.0,
        markersAnchor: 0.7,
        //markerMargin: const EdgeInsets.symmetric(horizontal: 0.3),
        markersAlignment: Alignment.bottomCenter,
        markersMaxCount: 4,
        markerDecoration: const BoxDecoration(
          color: Colors.black,
          shape: BoxShape.circle,
        ),
      ),
    );
  }
}
