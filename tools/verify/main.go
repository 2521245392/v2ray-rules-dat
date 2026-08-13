package main

import (
	"flag"
	"fmt"
	"os"
	"sort"
	"strings"

	router "github.com/v2fly/v2ray-core/v5/app/router/routercommon"
	"google.golang.org/protobuf/proto"
)

func main() {
	file := flag.String("file", "", "path to geosite.dat")
	expect := flag.String("expect", "", "comma-separated expected category names")
	require := flag.String("require", "", "comma-separated category=value rules that must exist")
	forbid := flag.String("forbid", "", "comma-separated category=value rules that must not exist")
	flag.Parse()

	if *file == "" || *expect == "" {
		fmt.Fprintln(os.Stderr, "both --file and --expect are required")
		os.Exit(2)
	}

	payload, err := os.ReadFile(*file)
	if err != nil {
		fail(err)
	}
	var list router.GeoSiteList
	if err := proto.Unmarshal(payload, &list); err != nil {
		fail(err)
	}

	actual := make([]string, 0, len(list.Entry))
	for _, entry := range list.Entry {
		name := strings.ToLower(entry.CountryCode)
		actual = append(actual, name)
		fmt.Printf("%-12s %d rules\n", name, len(entry.Domain))
	}
	expected := strings.Split(strings.ToLower(*expect), ",")
	sort.Strings(actual)
	sort.Strings(expected)
	if strings.Join(actual, ",") != strings.Join(expected, ",") {
		fmt.Fprintf(os.Stderr, "category mismatch\nexpected: %v\nactual:   %v\n", expected, actual)
		os.Exit(1)
	}
	fmt.Printf("verified: exactly %d categories\n", len(actual))

	for _, item := range strings.Split(*require, ",") {
		if item == "" {
			continue
		}
		parts := strings.SplitN(item, "=", 2)
		if len(parts) != 2 || !containsRule(&list, parts[0], parts[1]) {
			fmt.Fprintf(os.Stderr, "required rule not found: %s\n", item)
			os.Exit(1)
		}
		fmt.Printf("verified required rule: %s\n", item)
	}

	for _, item := range strings.Split(*forbid, ",") {
		if item == "" {
			continue
		}
		parts := strings.SplitN(item, "=", 2)
		if len(parts) != 2 {
			fmt.Fprintf(os.Stderr, "invalid forbidden rule: %s\n", item)
			os.Exit(2)
		}
		if containsRule(&list, parts[0], parts[1]) {
			fmt.Fprintf(os.Stderr, "forbidden rule found: %s\n", item)
			os.Exit(1)
		}
	}
	fmt.Printf("verified: %d forbidden rules are absent\n", countItems(*forbid))
}

func countItems(value string) int {
	if value == "" {
		return 0
	}
	return len(strings.Split(value, ","))
}

func containsRule(list *router.GeoSiteList, category string, value string) bool {
	for _, entry := range list.Entry {
		if !strings.EqualFold(entry.CountryCode, category) {
			continue
		}
		for _, domain := range entry.Domain {
			if strings.EqualFold(domain.Value, value) {
				return true
			}
		}
	}
	return false
}

func fail(err error) {
	fmt.Fprintln(os.Stderr, err)
	os.Exit(1)
}
