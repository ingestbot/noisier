def load_all_domains(file_path):
    with open(file_path, "r") as f:
        return [line.strip() for line in f if line.strip()]


def load_bad_domains(file_path):
    bad_domains = set()
    with open(file_path, "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith("Invalid:"):
                domain = line.replace("Invalid:", "").strip()
                bad_domains.add(domain)
    return bad_domains


def clean_domains(all_file, bad_file, output_file):
    all_domains = load_all_domains(all_file)
    bad_domains = load_bad_domains(bad_file)

    cleaned = [d for d in all_domains if d not in bad_domains]

    with open(output_file, "w") as f:
        for domain in cleaned:
            f.write(domain + "\n")

    print(f"Original: {len(all_domains)}")
    print(f"Removed: {len(bad_domains)}")
    print(f"Cleaned: {len(cleaned)}")


if __name__ == "__main__":
    clean_domains("domains_all", "domains_bad", "domains_clean")
