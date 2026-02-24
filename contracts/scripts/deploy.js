const { ethers } = require("hardhat");

async function main() {
  console.log("ImmortalMind kontratı deploy ediliyor...");

  const [deployer] = await ethers.getSigners();
  console.log(`Deployer: ${deployer.address}`);

  const balance = await ethers.provider.getBalance(deployer.address);
  console.log(`Bakiye: ${ethers.formatEther(balance)} ETH`);

  const ImmortalMind = await ethers.getContractFactory("ImmortalMind");
  const contract = await ImmortalMind.deploy();

  await contract.waitForDeployment();
  const address = await contract.getAddress();

  console.log(`\n✅ ImmortalMind deploy edildi: ${address}`);
  console.log(`\n.env dosyasına ekleyin:`);
  console.log(`BASE_CONTRACT_ADDRESS=${address}`);

  // Deployment bilgisini dosyaya kaydet
  const fs = require("fs");
  const deploymentInfo = {
    contract: "ImmortalMind",
    address: address,
    deployer: deployer.address,
    network: (await ethers.provider.getNetwork()).name,
    timestamp: new Date().toISOString(),
  };

  fs.writeFileSync(
    "deployment.json",
    JSON.stringify(deploymentInfo, null, 2)
  );
  console.log("\nDeployment bilgisi deployment.json dosyasına kaydedildi.");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
