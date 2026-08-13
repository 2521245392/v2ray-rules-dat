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
}

func fail(err error) {
	fmt.Fprintln(os.Stderr, err)
	os.Exit(1)
}
